import fs from 'fs'
import path from 'path'
import os from 'os'
import express from 'express'
import pino from 'pino'
import QRCode from 'qrcode'
import makeWASocket, {
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  DisconnectReason,
} from '@whiskeysockets/baileys'

import cors from 'cors'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
app.use(cors())

// 👉 para servir la carpeta "public" (donde está index.html)
app.use(express.static(path.join(__dirname, 'public')))

// ======================= Config/ENV =======================
const PORT = process.env.PORT || 3050
const INSTANCE_NAME   = process.env.INSTANCE_NAME || `${os.hostname()}-whatsapp-grupos`
const AUTH_DIR        = process.env.AUTH_DIR || `./auth-${INSTANCE_NAME}`
const HEARTBEAT_URL   = process.env.HEARTBEAT_URL   || ''            // ej: http://localhost:4000
const HEARTBEAT_TOKEN = process.env.HEARTBEAT_TOKEN || ''            // opcional
const WEBHOOK_URL     = process.env.WEBHOOK_URL     || ''            // si querés recibir mensajes
const FORWARD_FROM_ME  = String(process.env.FORWARD_FROM_ME || 'false').toLowerCase() === 'true'
const FORWARD_STATUSES = String(process.env.FORWARD_STATUSES || 'false').toLowerCase() === 'true'

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  base: null,
  timestamp: pino.stdTimeFunctions.isoTime,
})

// descarta pendientes muy viejos
const MAX_AGE_SEC      = 30
const MAX_BOOT_AGE_SEC = 30
const START_AT_SEC     = Math.floor(Date.now() / 1000)

const BURST_MS = Number(process.env.INCOMING_BURST_MS || 1500)
const SEEN_MAX = Number(process.env.SEEN_CACHE_MAX || 20000)

const lastByPhone = new Map()
const seenIds     = new Map()
setInterval(() => {
  const now = Date.now()
  if (seenIds.size <= SEEN_MAX) return
  for (const [id, ts] of seenIds) {
    if (now - ts > 60 * 60 * 1000) seenIds.delete(id)
    if (seenIds.size <= SEEN_MAX) break
  }
}, 60_000)

// ======================= Estado/health =======================
const health = {
  instance:   INSTANCE_NAME,
  pid:        process.pid,
  httpPort:   PORT,
  startedAt:  Date.now(),
  connected:  false,
  lastQR:     false,
  userJid:    null,
  pushName:   null,
  platform:   null,
  lastMessageAt: 0,
  messagesCount: 0,
  ackOk:      0,
  ackTimeout: 0,
}

// ======================= App HTTP =======================

app.use(express.json({ limit: '20mb' }))

let lastQRText = null

app.get('/health', (_req, res) => {
  res.json({
    ok: true,
    wa_connected: health.connected,
    instance: INSTANCE_NAME,
    userJid: health.userJid,
    pushName: health.pushName,
  })
})

app.get('/qr', async (_req, res) => {
  if (!lastQRText) {
    // si no hay QR pendiente, devolvemos un JSON para el front
    return res.json({ ok: false, qr: null })
  }

  const dataUrl = await QRCode.toDataURL(lastQRText)
  res.json({
    ok: true,
    qr: dataUrl,
  })
})

// ======================= Utilidades =======================
const sockRef = { current: null }
const getSock = () => {
  if (!sockRef.current) throw new Error('Socket no inicializado')
  return sockRef.current
}

const normalizeJid = (input) => {
  if (!input) return null
  const s = String(input)
  // si ya viene completo (personas o grupos) lo dejamos
  if (s.includes('@')) return s
  const digits = s.replace(/\D/g, '')
  if (!digits) return null
  return `${digits}@s.whatsapp.net`
}

function canonicalUserJid (jid) {
  const j = String(jid || '')
  if (!j.endsWith('@s.whatsapp.net')) return null
  const num = j.split('@')[0].split(':')[0]
  if (!/^\d{6,}$/.test(num)) return null
  return `${num}@s.whatsapp.net`
}

function extractInbound (m) {
  const msg = m?.message || {}
  const key = m?.key || {}
  const out = {
    messageId: key.id || null,
    from: key.remoteJid || null,
    sender: key.participant || null,
    fromMe: !!key.fromMe,
    type: 'unknown',
    text: null,
    optionId: null,
  }

  if (msg.templateButtonReplyMessage) {
    out.type = 'template_button'
    out.optionId = msg.templateButtonReplyMessage.selectedId || null
    out.text = msg.templateButtonReplyMessage.selectedDisplayText || null
    return out
  }
  if (msg.buttonsResponseMessage) {
    out.type = 'buttons'
    out.optionId = msg.buttonsResponseMessage.selectedButtonId || null
    out.text = msg.buttonsResponseMessage.selectedDisplayText || null
    return out
  }
  if (msg.listResponseMessage) {
    out.type = 'list'
    const sel = msg.listResponseMessage.singleSelectReply
    out.optionId = sel?.selectedRowId || null
    out.text = sel?.selectedRowId || null
    return out
  }
  if (msg.conversation)              { out.type = 'text'; out.text = msg.conversation; return out }
  if (msg.extendedTextMessage?.text) { out.type = 'text'; out.text = msg.extendedTextMessage.text; return out }
  if (msg.imageMessage)              { out.type = 'image';   out.text = msg.imageMessage.caption || null; return out }
  if (msg.documentMessage)           { out.type = 'document';out.text = msg.documentMessage.caption || null; return out }
  if (msg.videoMessage)              { out.type = 'video';   out.text = msg.videoMessage.caption || null; return out }
  if (msg.audioMessage)              { out.type = 'audio';   return out }
  return out
}

const parseMaybeJson = (v) => {
  if (!v) return null
  if (Array.isArray(v) || typeof v === 'object') return v
  if (typeof v === 'string') { try { return JSON.parse(v) } catch { return null } }
  return null
}

function waitForAck (sock, id, timeoutMs = 12000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      sock.ev.off('messages.update', onUpd)
      health.ackTimeout++
      reject(new Error('ack_timeout'))
    }, timeoutMs)

    const onUpd = (updates) => {
      for (const u of updates) {
        const st = u.update?.status ?? u.status
        if (u.key?.id === id && typeof st === 'number') {
          clearTimeout(timer)
          sock.ev.off('messages.update', onUpd)
          if (st >= 2) health.ackOk++
          return resolve(st)
        }
      }
    }
    sock.ev.on('messages.update', onUpd)
  })
}

// ======================= Arranque WA =======================
async function startSock () {
  logger.info('[auth] dir = ' + AUTH_DIR)
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR)
  const { version } = await fetchLatestBaileysVersion()

  const sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false,
    logger,
    connectTimeoutMs: 20000,
    keepAliveIntervalMs: 20000,
    markOnlineOnConnect: false,
    syncFullHistory: false,
  })

  sockRef.current = sock
  sock.ev.on('creds.update', saveCreds)

  sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      lastQRText = qr
      health.lastQR = true
      logger.info('📲 QR actualizado, abrí /qr para escanearlo')
    }

    if (connection === 'open') {
      lastQRText = null
      health.lastQR = false
      health.connected = true
      health.userJid   = sock.user?.id   || null
      health.pushName  = sock.user?.name || null
      health.platform  = sock.user?.platform || null
      logger.info(`✅ Conectado a WhatsApp: ${health.userJid} - ${health.pushName || ''}`)
      return
    }

    if (connection === 'close') {
      health.connected = false

      const err    = lastDisconnect?.error
      const boom   = err?.output?.payload || {}
      const status = err?.output?.statusCode
      logger.warn({
        status,
        boomMessage: boom.message,
        boomError: boom.error,
        code: err?.code || err?.cause?.code || undefined,
      }, '🔌 Conexión cerrada')

      const isEconnreset = (String(err?.code || err?.cause?.code || '').toUpperCase() === 'ECONNRESET')
      const delayMs =
        isEconnreset ? 30000 :
        (status && status !== DisconnectReason.loggedOut ? 10000 : 0)
      const shouldReconnect = status !== DisconnectReason.loggedOut

      sockRef.current = null

      if (shouldReconnect) {
        if (delayMs > 0) logger.info({ delayMs }, '⏳ Reintentando conexión en…')
        setTimeout(() => {
          startSock().catch(e => logger.error(e))
        }, delayMs)
      } else {
        logger.error('❌ Sesión cerrada (loggedOut). Borrá la carpeta de auth y re-vinculá.')
      }
    }
  })

  // Handler de mensajes entrantes (si querés usar WEBHOOK_URL)
  sock.ev.on('messages.upsert', async ({ type, messages }) => {
    try {
      if (type !== 'notify' || !messages?.length) return

      for (const m of messages) {
        const jid = m.key?.remoteJid || ''
        const id  = m.key?.id || ''

        if (id && seenIds.has(id)) continue
        if (id) seenIds.set(id, Date.now())

        if (!FORWARD_STATUSES && jid.endsWith('@status.broadcast')) continue
        if (jid.endsWith('@g.us')) continue          // ← ignoramos grupos entrantes
        if (m.key?.fromMe && !FORWARD_FROM_ME) continue

        const phone = canonicalUserJid(jid)
        if (!phone) continue

        const nowMs  = Date.now()
        const nowSec = Math.floor(nowMs / 1000)
        const ts     = Number(m.messageTimestamp) || 0

        const ageNow  = ts ? (nowSec     - ts) : 0
        const ageBoot = ts ? (START_AT_SEC - ts) : 0

        if (ts && ageNow > MAX_AGE_SEC) {
          logger.info({ phone, ts, ageNow }, 'skip old (live)')
          continue
        }
        if (ts && ageBoot > MAX_BOOT_AGE_SEC) {
          logger.info({ phone, ts, ageBoot }, 'skip old (boot backlog)')
          continue
        }

        const last = lastByPhone.get(phone) || 0
        if (nowMs - last < BURST_MS) {
          logger.info({ phone, delta: nowMs - last }, 'skip burst')
          continue
        }
        lastByPhone.set(phone, nowMs)

        const norm = extractInbound(m)
        norm.phone = phone
        norm.from  = phone
        norm.name  = m.pushName || phone.split('@')[0]
        norm.baileysEventType = type
        norm.meta  = {
          ts,
          ageSec: Math.max(ageNow, 0),
          receivedAt: nowMs,
        }

        health.lastMessageAt = nowMs
        health.messagesCount++

        if (!WEBHOOK_URL) continue
        await fetch(WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(norm),
        })
      }
    } catch (e) {
      logger.warn({ err: String(e) }, 'upsert handler error')
    }
  })

  // Heartbeat opcional
  async function sendHeartbeat () {
    if (!HEARTBEAT_URL) return
    try {
      await fetch(`${HEARTBEAT_URL}/hb`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(HEARTBEAT_TOKEN ? { 'x-auth': HEARTBEAT_TOKEN } : {}),
        },
        body: JSON.stringify(health),
      })
    } catch {}
  }
  setInterval(sendHeartbeat, 10_000)
}

// ======================= API de envío =======================
// Sirve tanto para personas como para GRUPOS, usando "jid"
app.post('/send', async (req, res) => {
  try {
    const sock = getSock()
    const {
      jid,
      phone,
      text,
      footer,
      mentions = [],
      quotedId,
      buttons,
      templateButtons,
    } = req.body || {}

    if (!text)  return res.status(400).json({ ok:false, error:'Falta "text"' })
    const target = normalizeJid(jid || phone)
    if (!target) return res.status(400).json({ ok:false, error:'Falta "jid" o "phone"' })

    const options = {}
    const mentionJids = (mentions || []).map(normalizeJid).filter(Boolean)
    if (mentionJids.length) options.mentions = mentionJids
    if (quotedId) options.quoted = { key: { id: quotedId, remoteJid: target } }

    const msg = { text: String(text) }
    if (footer) msg.footer = String(footer)

    const tb   = parseMaybeJson(templateButtons)
    const btns = parseMaybeJson(buttons)

    if (Array.isArray(btns) && btns.length) {
      msg.buttons = btns
      msg.headerType = 1
    } else if (Array.isArray(tb) && tb.length) {
      msg.templateButtons = tb
    }

    logger.info({ to: target }, '[send]')
    const resp = await sock.sendMessage(target, msg, options)

    // Esperamos el ACK, pero si se pasa de tiempo NO rompemos la API
    try {
      await waitForAck(sock, resp?.key?.id)
    } catch (e) {
      if (e?.message === 'ack_timeout') {
        logger.warn(
          { to: target, id: resp?.key?.id },
          '[send] ack_timeout, continuamos igual'
        )
        // NO relanzamos el error
      } else {
        throw e       // otros errores sí se reportan
      }
    }

    res.json({ ok:true, messageId: resp?.key?.id || null, legacy:false })

  } catch (err) {
    logger.error({ err }, '[send] ERROR')
    res.status(500).json({ ok:false, error: err?.message || 'Error interno' })
  }
})

// Envío de archivo (lo vamos a usar para las tarjetas de cumple)
app.post('/sendFile', async (req, res) => {
  try {
    const sock = getSock()
    let {
      jid,
      phone,
      url,
      filePath,
      fileName,
      caption,
      mimetype,
      fileBase64,
    } = req.body || {}

    phone    = typeof phone    === 'string' ? phone.trim()    : ''
    jid      = typeof jid      === 'string' ? jid.trim()      : ''
    url      = typeof url      === 'string' ? url.trim()      : ''
    filePath = typeof filePath === 'string' ? filePath.trim() : ''
    fileName = typeof fileName === 'string' ? fileName.trim() : 'archivo'
    caption  = typeof caption  === 'string' ? caption         : ''
    mimetype = typeof mimetype === 'string' ? mimetype        : 'application/octet-stream'
    fileBase64 = typeof fileBase64 === 'string' ? fileBase64.trim() : ''

    const target = normalizeJid(jid || phone)
    if (!target) {
      console.log('sendFile: falta jid/phone')
      return res.status(400).json({ ok:false, error:'Falta "jid" o "phone"' })
    }

    console.log('sendFile target:', target)

    const hasUrl  = !!url
    const hasPath = !!filePath
    const hasB64  = !!fileBase64

    if (!hasUrl && !hasPath && !hasB64) {
      console.log('sendFile: falta url/filePath/fileBase64')
      return res.status(400).json({
        ok:false,
        error:'Debes enviar "url", "filePath" o "fileBase64"',
      })
    }

    const payloadBase = { caption }

    if (hasUrl) {
      console.log('sendFile: enviando desde URL ->', url)
      await sock.sendMessage(target, {
        ...payloadBase,
        document: { url },
        mimetype,
        fileName,
      })

    } else if (hasPath) {
      console.log('sendFile: enviando desde filePath ->', filePath)
      const abs = path.isAbsolute(filePath) ? filePath : path.resolve(filePath)
      const stream = fs.createReadStream(abs)
      await sock.sendMessage(target, {
        ...payloadBase,
        document: stream,
        mimetype,
        fileName,
      })

    } else {
      // BASE64
      console.log('sendFile: enviando desde base64, tamaño:', fileBase64.length)
      const buffer = Buffer.from(fileBase64, 'base64')

      if (mimetype.startsWith('image/')) {
        // 👉 se envía como IMAGEN (preview, no adjunto)
        await sock.sendMessage(target, {
          ...payloadBase,
          image: buffer,
          mimetype,
        })
      } else {
        // 👉 cualquier otro archivo va como documento
        await sock.sendMessage(target, {
          ...payloadBase,
          document: buffer,
          mimetype,
          fileName,
        })
      }
    }

    res.json({ ok:true })
  } catch (e) {
    logger.error({ err: String(e) }, '[sendFile] error')
    res.status(400).json({ ok:false, error:String(e) })
  }
})

// ======================= Logout / reset sesión =======================
app.post('/logout', async (req, res) => {
  try {
    const sock = sockRef.current

    // 1) Cerrar sesión en WhatsApp si hay socket
    if (sock) {
      try {
        await sock.logout()
      } catch (e) {
        console.warn('Error haciendo logout():', e)
      }
    }

    // 2) Limpiar referencias en memoria
    sockRef.current   = null
    health.connected  = false
    health.userJid    = null
    health.pushName   = null
    lastQRText        = null
    health.lastQR     = false

    // 3) Borrar carpeta de autenticación (auth-INSTANCE_NAME)
    try {
      fs.rmSync(AUTH_DIR, { recursive: true, force: true })
      console.log('Carpeta de auth eliminada:', AUTH_DIR)
    } catch (e) {
      console.warn('No se pudo borrar AUTH_DIR:', e)
    }

    // 4) Volver a iniciar el socket para que genere un nuevo QR
    startSock().catch(e => console.error('Error reiniciando Baileys:', e))

    res.json({ ok: true })
  } catch (e) {
    console.error('Error en /logout:', e)
    res.status(500).json({ ok: false, error: 'logout_error' })
  }
})

// ======================= Listar grupos =======================
app.get('/groups', async (req, res) => {
  try {
    const sock = getSock()
    const groupsMap = await sock.groupFetchAllParticipating()
    const groups = Object.values(groupsMap).map(g => ({
      id: g.id,          // 👈 ESTE es el JID que necesitamos
      name: g.subject,   // nombre del grupo
    }))
    res.json({ ok: true, groups })
  } catch (e) {
    console.error('Error en /groups:', e)
    res.status(500).json({ ok: false, error: 'groups_error' })
  }
})


// ======================= Run =======================

app.listen(PORT, () => {
  console.log(`Servidor HTTP escuchando en puerto ${PORT}`)
  console.log(`Abrí en el navegador: http://localhost:${PORT}`)
  // arrancamos el socket de WhatsApp
  startSock().catch(e => {
    console.error('Error iniciando Baileys:', e)
  })
})
