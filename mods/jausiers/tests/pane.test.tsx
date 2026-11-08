import { expect, test } from 'claude-code/testing'

const PANE = {
  plugin: 'jausiers',
  component: 'Pane',
  requestId: 'jausiers',
  props: {
    title: 'Saint-Nicolas-de-Myre · Jausiers',
    isFocused: false,
    bodyColumns: 80,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 60 },
    view: {},
  },
} as const

// Un risultato di sole.py ridotto: una vetrata, un giorno.
const risultato = (facciata: number, asse: number | null, da: string, minuti: number) =>
  JSON.stringify({
    fonte_azimut: asse === null ? 'modello' : 'asse',
    asse_input: asse,
    facciata_az: facciata,
    abside_az: (facciata + 180) % 360,
    rotazione_vs_modello: facciata - 160,
    giorni: [
      {
        etichetta: 'Oggi',
        data: '2026-11-06',
        alba: '07:20',
        tramonto: '17:10',
        culminazione: { ora: '12:20', alt: 29.5, az: 180.9 },
        vetrate: [{ nome: 'Facciata - finestra centrale', da, a: '14:00', minuti }],
      },
    ],
  })

test('piantine come base, ricerca online come confronto', async ($, on) => {
  on('command.register', () => ({ value: { command: 'chiesa' } }))
  on('tool.register', () => ({ value: { tool: 'mcp__jausiers__salva_ricerca' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  const scritti: string[] = []
  on('fs.write', (_, e) => {
    scritti.push(JSON.stringify(e))
    return { value: undefined }
  })
  const calcoli: string[][] = []
  on('process.run', (_, e) => {
    const argv = [...(e as unknown as { argv: string[] }).argv]
    calcoli.push(argv)
    const online = argv.includes('--asse')
    return {
      value: {
        exitCode: 0,
        stdout: online ? risultato(156.2, 156.2, '10:10', 220) : risultato(160, null, '10:00', 240),
        stderr: '',
      },
    }
  })
  const avvii: string[][] = []
  on('process.spawn', async function* (_, e) {
    avvii.push([...e.argv])
    return { value: { code: 0, signal: null } }
  })
  on('clock.now', () => ({ value: 1_793_000_000_000 }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  // all'avvio: vista 3D sulle piantine, senza --asse
  expect(avvii.length).toBe(1)
  expect(avvii[0]?.some(a => a.endsWith('/scripts/viewer.py'))).toBe(true)
  expect(avvii[0]?.includes('--asse')).toBe(false)

  const ran = await $.tool.call({
    tool: 'mcp__jausiers__salva_ricerca',
    azimut_asse: 156.2,
    orientamento: 'Asse NNW-SSE.',
    storia: 'Costruita nel XIX secolo.',
    orientamento_fr: 'Axe NNO-SSE.',
    storia_fr: 'Construite au XIXe siècle.',
    fonti: [{ titolo: 'OSM', url: 'https://www.openstreetmap.org/way/93932532' }],
  })
  expect(JSON.stringify(ran)).toContain('piantine 160° contro online 156.2°')
  // la ricerca va anche nel sito, e la vista 3D resta sulle piantine
  expect(scritti.some(w => w.includes('/sito/comune/dati/ricerca.js') && w.includes('storia_fr') && w.includes('window.RICERCA'))).toBe(true)
  expect(avvii.length).toBe(1)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /^Asse online: / }))?.text).toBe('Asse online: 156.2°')
    expect((await ui.find({ type: 'Text', text: /^Piantine: facciata/ }))?.text).toContain('160°')
    const riga = await ui.find({ type: 'Text', text: /Facciata - finestra centrale/ })
    expect(riga?.text).toContain('10:00–14:00')
    expect(riga?.text).toContain('online 10:10–14:00 (-20 min)')
    await ui.press({ key: 'vistaOnline' })
    await ui.unmount()
  }
  // il pulsante "Online" apre la vista 3D ruotata
  expect(avvii.at(-1)?.slice(-2)).toEqual(['--asse', '156.2'])
  // ogni calcolo con un asse è affiancato da uno con le piantine
  expect(calcoli.filter(a => !a.includes('--asse')).length).toBeGreaterThanOrEqual(calcoli.filter(a => a.includes('--asse')).length)
})
