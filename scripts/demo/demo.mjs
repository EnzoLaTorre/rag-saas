// Genera docs/demo.gif recorriendo la app desplegada (o local) con Playwright.
//
// Variables de entorno:
//   BASE_URL        URL de la app (por defecto: https://rag-saas-psi.vercel.app)
//   DEMO_EMAIL      usuario demo (por defecto: demo@example.com)
//   DEMO_PASSWORD   contraseña demo (por defecto: demo1234)
//   OUT_GIF         ruta de salida (por defecto: ../../docs/demo.gif)
//   FPS             fotogramas por segundo del GIF (por defecto: 10)
//   MAX_SECONDS     duración máxima del GIF en segundos (por defecto: 55)
//
// Requiere: "npm install" en esta carpeta y "npx playwright install chromium".

import { spawn } from 'node:child_process'
import { mkdir, readdir, rm } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'
import ffmpegPath from 'ffmpeg-static'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..')
const BASE_URL = process.env.BASE_URL ?? 'https://rag-saas-psi.vercel.app'
const EMAIL = process.env.DEMO_EMAIL ?? 'demo@example.com'
const PASSWORD = process.env.DEMO_PASSWORD ?? 'demo1234'
const OUT_GIF = path.resolve(process.env.OUT_GIF ?? path.join(ROOT, 'docs', 'demo.gif'))
const FPS = Number(process.env.FPS ?? 10)
const MAX_SECONDS = Number(process.env.MAX_SECONDS ?? 55)
const TMP = path.join(ROOT, 'scripts', 'demo', '.tmp')

function log(msg) {
  console.log(`[demo] ${msg}`)
}

async function run(cmd, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { stdio: ['ignore', 'inherit', 'inherit'] })
    child.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`${cmd} salió con código ${code}`))))
  })
}

async function stopVideo(page) {
  await page.context().close()
  const video = page.video()
  if (!video) throw new Error('No se grabó video (falta recordVideo)')
  const files = await readdir(TMP)
  const webm = files.find((f) => f.endsWith('.webm'))
  if (!webm) throw new Error('No se encontró el .webm grabado')
  return path.join(TMP, webm)
}

async function toGif(webm) {
  if (!ffmpegPath) throw new Error('ffmpeg-static no resolvió un binario')
  await mkdir(path.dirname(OUT_GIF), { recursive: true })
  const palette = path.join(TMP, 'palette.png')
  const base = `fps=${FPS},scale=720:-1:flags=lanczos,trim=duration=${MAX_SECONDS},setpts=PTS-STARTPTS`
  await run(ffmpegPath, ['-y', '-i', webm, '-vf', `${base},palettegen=max_colors=128`, palette])
  await run(ffmpegPath, [
    '-y', '-i', webm, '-i', palette,
    '-lavfi', `${base}[x];[x][1:v]paletteuse=dither=bayer`,
    '-loop', '0', OUT_GIF,
  ])
}

await mkdir(TMP, { recursive: true })

const browser = await chromium.launch()
const context = await browser.newContext({
  viewport: { width: 1280, height: 800 },
  recordVideo: { dir: TMP, size: { width: 1280, height: 800 } },
})
const page = await context.newPage()
page.setDefaultTimeout(120_000)
page.setDefaultNavigationTimeout(120_000)

try {
  log(`Abriendo ${BASE_URL} (puede tardar si Railway se quedó dormido)`)
  await page.goto(BASE_URL)
  await page.locator('form.auth-card').waitFor()

  log('Iniciando sesión con la cuenta demo')
  await page.locator('input[type=email]').fill(EMAIL)
  await page.locator('input[type=password]').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()

  log('Esperando el listado de documentos')
  await page.getByRole('heading', { name: 'Mis documentos' }).waitFor()
  await page.locator('.doc-item').first().waitFor()
  await page.waitForTimeout(1200)

  log('Abriendo el chat')
  await page.getByRole('link', { name: 'Chat' }).click()
  await page.getByRole('heading', { name: 'Chat con tus documentos' }).waitFor()
  await page.waitForTimeout(800)

  const question = '¿Qué es RAG y para qué sirve?'
  log(`Preguntando: "${question}"`)
  await page.locator('.chat-input input').fill(question)
  await page.getByRole('button', { name: 'Enviar' }).click()

  log('Esperando la respuesta en streaming')
  await page.locator('.message.assistant .markdown').waitFor()
  await page.locator('.chat-input button').waitFor({ state: 'visible' })
  await page.waitForFunction(() => !document.body.innerText.includes('Escribiendo…'))
  await page.waitForTimeout(1500)

  log('Desplegando las fuentes citadas')
  await page.locator('.message.assistant .sources details').first().click()
  await page.waitForTimeout(1600)
  await page.locator('.message.assistant .sources details').first().click()

  log('Mostrando el historial')
  await page.getByRole('button', { name: /Historial/ }).click()
  await page.locator('.history-item').first().waitFor()
  await page.waitForTimeout(1400)

  log('Fin del recorrido; procesando video')
} finally {
  const webm = await stopVideo(page)
  await browser.close()
  await toGif(webm)
  await rm(TMP, { recursive: true, force: true })
  log(`GIF generado en ${OUT_GIF}`)
}