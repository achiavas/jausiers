import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Fonte, Ricerca, RisultatoSole, Sole, Vista } from '../types'

// ------------------------------------------------------------------ costanti
const PANE = 'jausiers'
const TITLE = 'Saint-Nicolas-de-Myre · Jausiers'
const TOOL_SHORT = 'salva_ricerca'
const TOOL = 'mcp__jausiers__salva_ricerca'
// Python con numpy + shapely (il /usr/bin/python3 di sistema non li ha).
const PYTHON = '/usr/local/bin/python3'
const FILE_BASE = 'ricerca_saint_nicolas_jausiers'

const ricerca = atom({ plugin: 'jausiers', key: 'ricerca' } as const, { stato: 'vuota', fonti: [] } as Ricerca, {
  shape: 'ricerca-1',
})
const sole = atom({ plugin: 'jausiers', key: 'sole' } as const, { stato: 'mai' } as Sole, { shape: 'sole-2' })
const giorno = atom({ plugin: 'jausiers', key: 'giorno' } as const, 0)
const vista = atom({ plugin: 'jausiers', key: 'vista' } as const, { stato: 'chiusa' } as Vista, { shape: 'vista-1' })

// mods/jausiers -> eglise_jausiers
const progetto = ($: EngineInterface) => $.plugin.root.replace(/\/mods\/[^/]+\/?$/, '')
const cartellaOrientamento = ($: EngineInterface) => `${progetto($)}/orientatamento_chiese_Ubaye`
// Il sito legge la ricerca da qui (stesso formato di sito/strumenti/genera_dati.py)
const fileSito = ($: EngineInterface) => `${progetto($)}/sito/comune/dati/ricerca.js`

const adesso = async ($: EngineInterface) => new Date(await $.clock.now()).toISOString()

// ------------------------------------------------------------------ blocco 1: ricerca
const SCHEMA = {
  type: 'object',
  properties: {
    azimut_asse: {
      type: 'number',
      description:
        "Azimut dell'asse lungo della chiesa in gradi da nord geografico, senso orario (0-360). Ometti se nessuna fonte lo dà.",
    },
    azimut_abside: {
      type: 'number',
      description: "Azimut verso cui è rivolta l'abside (0-360), se una fonte lo indica.",
    },
    orientamento: {
      type: 'string',
      description: "Sintesi sull'orientamento: valore, come è stato misurato, discrepanze tra fonti.",
    },
    storia: { type: 'string', description: 'Sintesi storica (date, costruzione, ricostruzioni, architetti, restauri).' },
    affidabilita: { type: 'string', description: "Quanto sono affidabili i valori trovati e perché." },
    orientamento_fr: { type: 'string', description: 'Lo stesso testo di orientamento, in francese.' },
    storia_fr: { type: 'string', description: 'La stessa sintesi storica, in francese.' },
    affidabilita_fr: { type: 'string', description: "L'affidabilità, in francese." },
    fonti: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          titolo: { type: 'string' },
          url: { type: 'string' },
          nota: { type: 'string', description: 'Cosa sostiene questa fonte (italiano).' },
          nota_fr: { type: 'string', description: 'La stessa nota in francese.' },
        },
        required: ['titolo', 'url'],
      },
    },
  },
  required: ['orientamento', 'storia', 'fonti', 'orientamento_fr', 'storia_fr'],
}

const PROMPT_RICERCA = `Ricerca per il pannello "jausiers" (Église Saint-Nicolas-de-Myre, Jausiers, Alpes-de-Haute-Provence, valle dell'Ubaye).

Cerca sul web (WebSearch / WebFetch: Mérimée/POP, Wikipedia FR, sito del comune, patrimoine/inventaire PACA, OpenStreetMap, articoli e guide) e raccogli:
1. ORIENTAMENTO: l'azimut dell'asse della chiesa (gradi da nord, senso orario) e verso dove guarda l'abside. Se nessuna fonte dà un numero, puoi ricavarlo dalla geometria OSM (way 93932532) e dichiararlo come misura derivata.
   Riferimenti già nel progetto, da confermare o smentire: OSM/rettangolo minimo ≈ 156.2° (asse modulo 180, in orientatamento_chiese_Ubaye/orientamento_chiese.csv); piantine cartacee (diagnostico 2016, base del modello 3D): facciata ≈ 160° (SSE), abside ≈ 340° (NNW). Le misure della chiesa vengono dalle piantine: il valore online serve come confronto, quindi segnala chiaramente se e di quanto si discosta.
2. STORIA: costruzione, date, architetto, stile, campanile, restauri, protezione Monuments historiques.

Ogni affermazione deve avere una fonte con URL. Il sito ha una versione italiana e una francese, ognuna in una lingua sola: scrivi orientamento, storia, affidabilità e note delle fonti in italiano E in francese (campi *_fr), senza mescolare le lingue nello stesso testo. Alla fine chiama UNA volta lo strumento ${TOOL} con azimut_asse (se trovato), azimut_abside, orientamento, storia, affidabilita e fonti. Poi riassumi in due righe.`

async function avviaRicerca($: EngineInterface) {
  await $.tool.register({
    name: TOOL_SHORT,
    description:
      "Salva i risultati della ricerca su Saint-Nicolas-de-Myre di Jausiers (orientamento, storia, fonti) nel pannello jausiers, in orientatamento_chiese_Ubaye e nel sito; se c'è un azimut lo confronta con le piantine nel calcolo solare.",
    inputSchema: SCHEMA,
    isDeferred: false,
  })
  await update($, ricerca, r => ({ ...r, stato: 'in_corso' }))
  void $.ui.open({ id: PANE, title: TITLE })
  await $.prompt.submit({ text: PROMPT_RICERCA })
}

const num = (x: unknown) => (typeof x === 'number' && Number.isFinite(x) ? x : undefined)
const str = (x: unknown) => (typeof x === 'string' ? x : '')

function markdown(r: Ricerca) {
  const righe = [
    '# Église Saint-Nicolas-de-Myre, Jausiers — ricerca',
    '',
    `Aggiornato: ${r.aggiornato}`,
    '',
    '## Orientamento',
    '',
    `- Azimut asse: ${r.azimutAsse ?? 'non trovato'}°`,
    `- Azimut abside: ${r.azimutAbside ?? 'non indicato'}${r.azimutAbside === undefined ? '' : '°'}`,
    '',
    r.orientamento ?? '',
    '',
    '## Storia',
    '',
    r.storia ?? '',
    '',
    '## Affidabilità',
    '',
    r.affidabilita || '—',
    '',
    '## Fonti',
    '',
    ...r.fonti.map(f => `- [${f.titolo}](${f.url})${f.nota ? ` — ${f.nota}` : ''}`),
    '',
  ]
  return righe.join('\n')
}

// ------------------------------------------------------------------ blocco 2: sole
let coda: Promise<void> = Promise.resolve()

async function eseguiSole($: EngineInterface, asse: number | undefined): Promise<RisultatoSole> {
  const argv = [PYTHON, `${$.plugin.root}/scripts/sole.py`, '--src', `${progetto($)}/jausiers_sun3d_py`]
  if (asse !== undefined) argv.push('--asse', String(asse))
  const { exitCode, stdout, stderr } = await $.process.run(argv, { timeoutMs: 180_000 })
  if (exitCode !== 0) throw new Error(`exit ${exitCode}: ${stderr.trim().split('\n').slice(-3).join(' ')}`)
  return JSON.parse(stdout) as RisultatoSole
}

/** Piantine sempre (la base); con un asse online anche il confronto. */
function calcola($: EngineInterface, asseOnline: number | undefined): Promise<void> {
  coda = coda.then(async () => {
    await update($, sole, s => ({ ...s, stato: 'calcolo', asseOnline, errore: undefined }))
    const t0 = await $.clock.now()
    try {
      const piantine = await eseguiSole($, undefined)
      const online = asseOnline === undefined ? undefined : await eseguiSole($, asseOnline)
      const durataMs = (await $.clock.now()) - t0
      const aggiornato = await adesso($)
      await update($, sole, () => ({ stato: 'ok', piantine, online, asseOnline, durataMs, aggiornato }))
    } catch (err) {
      const errore = err instanceof Error ? err.message : String(err)
      await update($, sole, s => ({ ...s, stato: 'errore', errore }))
    }
  }).catch(() => undefined) // la coda non si blocca mai su un errore
  return coda
}

const minuti = (hhmm: string) => Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5))

// ------------------------------------------------------------------ vista 3D (viewer_3d.py)
// Il figlio vive finché la finestra è aperta; chiuderla, un nuovo azimut o lo
// scaricamento del modulo lo terminano.
let finestra: ReturnType<EngineInterface['process']['spawn']> | undefined

async function chiudiVista($: EngineInterface) {
  const vecchia = finestra
  finestra = undefined
  if (vecchia) await vecchia.return({ code: null, signal: null }).catch(() => undefined)
  await update($, vista, v => ({ ...v, stato: 'chiusa' }))
}

async function apriVista($: EngineInterface, asse: number | undefined) {
  if (finestra) await chiudiVista($)
  const argv = [PYTHON, `${$.plugin.root}/scripts/viewer.py`, '--src', `${progetto($)}/jausiers_sun3d_py`]
  if (asse !== undefined) argv.push('--asse', String(asse))
  const figlio = $.process.spawn({ argv })
  finestra = figlio
  await update($, vista, () => ({ stato: 'aperta', asse }))
  void (async () => {
    let coda = ''
    let errore: string | undefined
    try {
      for await (const pezzo of figlio) if (pezzo.stream === 'stderr') coda = (coda + pezzo.text).slice(-600)
      const { code } = await figlio.result
      if (code !== 0 && code !== null) errore = `exit ${code}: ${coda.trim().split('\n').slice(-2).join(' ')}`
    } catch (err) {
      errore = err instanceof Error ? err.message : String(err)
    }
    if (finestra !== figlio) return // sostituita da una nuova finestra
    finestra = undefined
    await update($, vista, v => ({ ...v, stato: errore ? 'errore' : 'chiusa', errore }))
  })().catch(() => undefined)
}

// ------------------------------------------------------------------ registrazione
export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await $.command.register({
      name: 'chiesa',
      description: 'Ricerca web su orientamento e storia di Saint-Nicolas-de-Myre (Jausiers) e ricalcolo solare',
    })
    const r = await read($, ricerca)
    // Un reload perde lo strumento: lo ridichiaro se una ricerca è già partita.
    if (r.stato !== 'vuota') {
      await $.tool.register({
        name: TOOL_SHORT,
        description: 'Salva i risultati della ricerca su Saint-Nicolas-de-Myre di Jausiers nel pannello jausiers.',
        inputSchema: SCHEMA,
        isDeferred: false,
      })
    }
    const s = await read($, sole)
    if (s.stato !== 'ok') void calcola($, r.azimutAsse)
    await apriVista($, undefined) // le piantine sono la base
    return started
  })

  on('command.run', { command: 'chiesa' }, async $ => {
    await avviaRicerca($)
    return { text: 'Pannello aperto, strumento salva_ricerca registrato: la ricerca parte al prossimo turno.' }
  })

  on('tool.call', { tool: TOOL }, async ($, e) => {
    const fonti: Fonte[] = (Array.isArray(e.fonti) ? e.fonti : [])
      .filter((f): f is Record<string, unknown> => typeof f === 'object' && f !== null)
      .map(f => ({
        titolo: str(f.titolo) || str(f.url),
        url: str(f.url),
        nota: str(f.nota) || undefined,
        nota_fr: str(f.nota_fr) || undefined,
      }))
      .filter(f => f.url)
    const nuova: Ricerca = {
      stato: 'salvata',
      azimutAsse: num(e.azimut_asse),
      azimutAbside: num(e.azimut_abside),
      orientamento: str(e.orientamento),
      storia: str(e.storia),
      affidabilita: str(e.affidabilita) || undefined,
      orientamento_fr: str(e.orientamento_fr) || undefined,
      storia_fr: str(e.storia_fr) || undefined,
      affidabilita_fr: str(e.affidabilita_fr) || undefined,
      fonti,
      file: `${cartellaOrientamento($)}/${FILE_BASE}.md`,
      aggiornato: await adesso($),
    }
    await $.fs.write(nuova.file!, markdown(nuova))
    await $.fs.write(`${cartellaOrientamento($)}/${FILE_BASE}.json`, JSON.stringify(nuova, null, 2) + '\n')
    await $.fs.write(
      fileSito($),
      `// Generato dal mod jausiers (salva_ricerca): non modificare a mano.\nwindow.RICERCA = ${JSON.stringify(nuova, null, 1)};\n`,
    )
    await update($, ricerca, () => nuova)

    let nota = 'Nessun azimut: resta il calcolo con le piantine.'
    const s = await read($, sole)
    if (nuova.azimutAsse !== undefined) {
      const cambiato = s.asseOnline === undefined || Math.abs(s.asseOnline - nuova.azimutAsse) > 0.05
      if (cambiato || s.stato !== 'ok') {
        void calcola($, nuova.azimutAsse)
        nota = `Confronto solare avviato: piantine 160° contro online ${nuova.azimutAsse}°. La vista 3D resta sulle piantine.`
      } else {
        nota = `Asse online ${nuova.azimutAsse}° già confrontato.`
      }
    }
    void $.ui.open({ id: PANE, title: TITLE })
    return { result: `Salvato: ${nuova.file} (+ .json) e sito/comune/dati/ricerca.js, ${fonti.length} fonti. ${nota}` }
  }).catch(($, e, next) =>
    next.called ? next(e) : { deny: 'salva_ricerca non è riuscito a salvare: riprova con campi validi.' },
  )

  // ---------------------------------------------------------------- pannello
  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const els = $.ui.resolve(e)
    const { Box, Text, Button } = els
    const Link = 'Link' in els ? els.Link : undefined
    const r = await read($, ricerca)
    const s = await read($, sole)
    const g = await read($, giorno)
    const w = e.props.bodyColumns

    const fonte = (f: Fonte, i: number) => (
      <Box key={`f${i}`} flexDirection="column">
        {Link ? <Link href={f.url} label={f.titolo} /> : <Text>{f.titolo}</Text>}
        {!Link && <Text dimColor>{f.url}</Text>}
        {f.nota && <Text dimColor>{f.nota}</Text>}
      </Box>
    )

    const statoRicerca = {
      vuota: 'Nessuna ricerca. Usa /chiesa o il pulsante.',
      in_corso: 'Ricerca in corso…',
      salvata: `Salvata ${r.aggiornato?.slice(0, 16).replace('T', ' ') ?? ''}`,
    }[r.stato]

    const v = await read($, vista)
    const base = s.piantine
    const giorni = base?.giorni ?? []
    const i = Math.min(g, Math.max(0, giorni.length - 1))
    const sel = giorni[i]
    const selOnline = s.online?.giorni[i]
    const confronto = (nome: string) => {
      const o = selOnline?.vetrate.find(x => x.nome === nome)
      const p = sel?.vetrate.find(x => x.nome === nome)
      if (!selOnline) return ''
      if (!o) return '  online: nessuna luce'
      const d = o.minuti - (p?.minuti ?? 0)
      const spost = p ? minuti(o.da) - minuti(p.da) : 0
      return `  online ${o.da}–${o.a}${d ? ` (${d > 0 ? '+' : ''}${d} min)` : ''}${spost && !d ? ` (${spost > 0 ? '+' : ''}${spost} min)` : ''}`
    }
    const soloOnline = (selOnline?.vetrate ?? []).filter(o => !sel?.vetrate.some(p => p.nome === o.nome))

    return (
      <Box flexDirection="column" gap={1} width={w}>
        {/* ---------------- Blocco 1 ---------------- */}
        <Box flexDirection="column" borderStyle="round" paddingX={1}>
          <Text bold>1 · Ricerca: orientamento e storia</Text>
          <Text dimColor>{statoRicerca}</Text>
          {r.stato === 'salvata' && (
            <Box flexDirection="column">
              <Text>
                Asse online: <Text bold>{r.azimutAsse !== undefined ? `${r.azimutAsse}°` : 'non trovato'}</Text>
                {r.azimutAbside !== undefined ? `  ·  abside ${r.azimutAbside}°` : ''}
              </Text>
              {r.orientamento && <Text wrap="wrap">{r.orientamento}</Text>}
              <Text bold>Storia</Text>
              <Text wrap="wrap">{r.storia}</Text>
              {r.affidabilita && <Text dimColor wrap="wrap">Affidabilità: {r.affidabilita}</Text>}
              <Text bold>Fonti ({r.fonti.length})</Text>
              {r.fonti.map(fonte)}
              {r.file && <Text dimColor>File: {r.file.replace(progetto($) + '/', '')}</Text>}
            </Box>
          )}
          <Button
            key="ricerca"
            label={r.stato === 'vuota' ? 'Avvia ricerca' : 'Rifai ricerca'}
            onPress={() => avviaRicerca($)}
          />
        </Box>

        {/* ---------------- Blocco 2 ---------------- */}
        <Box flexDirection="column" borderStyle="round" paddingX={1}>
          <Text bold>2 · Sole attraverso le vetrate</Text>
          <Text dimColor>
            {s.stato === 'calcolo'
              ? `Calcolo in corso: piantine${s.asseOnline !== undefined ? ` e online (asse ${s.asseOnline}°)` : ''}…`
              : s.stato === 'errore'
                ? `Errore: ${s.errore}`
                : s.stato === 'mai'
                  ? 'Non ancora calcolato.'
                  : `Calcolato ${s.aggiornato?.slice(0, 16).replace('T', ' ') ?? ''} in ${((s.durataMs ?? 0) / 1000).toFixed(1)} s`}
          </Text>
          {base && (
            <Box flexDirection="column">
              <Text>
                Piantine: facciata <Text bold>{base.facciata_az}°</Text> · abside {base.abside_az}°
              </Text>
              {s.online && (
                <Text dimColor>
                  Confronto online: asse {s.online.asse_input}° → facciata {s.online.facciata_az}° (rotazione{' '}
                  {s.online.rotazione_vs_modello}°)
                </Text>
              )}
              <Box flexDirection="row" flexWrap="wrap" columnGap={1}>
                {giorni.map((d, k) => (
                  <Button
                    key={`g${k}`}
                    label={d.etichetta}
                    variant={k === i ? 'primary' : 'secondary'}
                    onPress={() => update($, giorno, () => k)}
                  />
                ))}
              </Box>
              {sel && (
                <Box flexDirection="column">
                  <Text>
                    {sel.data} · alba {sel.alba ?? '—'} · tramonto {sel.tramonto ?? '—'} · culmine{' '}
                    {sel.culminazione.ora} a {sel.culminazione.alt}°
                  </Text>
                  <Text bold>Vetrate illuminate, piantine ({sel.vetrate.length})</Text>
                  {sel.vetrate.length === 0 && <Text dimColor>nessuna</Text>}
                  {sel.vetrate.map((v, k) => (
                    <Text key={`v${k}`}>
                      {v.da}–{v.a} <Text dimColor>({v.minuti} min)</Text> {v.nome}
                      <Text dimColor>{confronto(v.nome)}</Text>
                    </Text>
                  ))}
                  {soloOnline.map((o, k) => (
                    <Text key={`o${k}`} dimColor>
                      solo online: {o.da}–{o.a} {o.nome}
                    </Text>
                  ))}
                </Box>
              )}
            </Box>
          )}
          <Box flexDirection="row" columnGap={1}>
            <Button key="ricalcola" label="Ricalcola" onPress={() => calcola($, r.azimutAsse)} />
          </Box>
        </Box>

        {/* ---------------- Blocco 3 ---------------- */}
        <Box flexDirection="column" borderStyle="round" paddingX={1}>
          <Text bold>3 · Vista 3D (viewer_3d.py)</Text>
          <Text dimColor>
            {v.stato === 'aperta'
              ? `Finestra aperta: ${v.asse !== undefined ? `confronto online, asse ${v.asse}°` : 'piantine (facciata 160°)'}`
              : v.stato === 'errore'
                ? `Errore: ${v.errore}`
                : 'Finestra chiusa.'}
          </Text>
          <Box flexDirection="row" columnGap={1}>
            <Button key="vista" label="Vista 3D (piantine)" onPress={() => apriVista($, undefined)} />
            {r.azimutAsse !== undefined && (
              <Button key="vistaOnline" label={`Online ${r.azimutAsse}°`} onPress={() => apriVista($, r.azimutAsse)} />
            )}
            {v.stato === 'aperta' && <Button key="chiudi" label="Chiudi" onPress={() => chiudiVista($)} />}
          </Box>
        </Box>
      </Box>
    )
  })
}
