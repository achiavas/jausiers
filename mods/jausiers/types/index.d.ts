export type Fonte = { titolo: string; url: string; nota?: string; nota_fr?: string }

export type Ricerca = {
  stato: 'vuota' | 'in_corso' | 'salvata'
  /** azimut dell'asse lungo, gradi da nord (anche modulo 180) */
  azimutAsse?: number
  /** azimut verso cui guarda l'abside, se la fonte lo dice */
  azimutAbside?: number
  orientamento?: string
  storia?: string
  affidabilita?: string
  /** stessi testi in francese, per sito/fr */
  orientamento_fr?: string
  storia_fr?: string
  affidabilita_fr?: string
  fonti: Fonte[]
  file?: string
  aggiornato?: string
}

export type VetrataLuce = { nome: string; da: string; a: string; minuti: number }

export type GiornoSole = {
  etichetta: string
  data: string
  alba: string | null
  tramonto: string | null
  culminazione: { ora?: string; alt: number; az?: number }
  vetrate: VetrataLuce[]
}

export type RisultatoSole = {
  fonte_azimut: 'asse' | 'facciata' | 'modello'
  asse_input: number | null
  facciata_az: number
  abside_az: number
  rotazione_vs_modello: number
  giorni: GiornoSole[]
}

export type Sole = {
  stato: 'mai' | 'calcolo' | 'ok' | 'errore'
  /** sole.py senza --asse: le misure delle piantine (facciata 160°), la base */
  piantine?: RisultatoSole
  /** sole.py --asse <asse online>: solo confronto */
  online?: RisultatoSole
  /** l'asse online con cui è stato fatto il confronto */
  asseOnline?: number
  errore?: string
  durataMs?: number
  aggiornato?: string
}

export type Vista = {
  stato: 'chiusa' | 'aperta' | 'errore'
  /** l'asse con cui è aperto viewer_3d.py; assente = modello (160) */
  asse?: number
  errore?: string
}

declare module 'claude-code' {
  interface PluginState {
    jausiers: { ricerca: Shaped<Ricerca>; sole: Shaped<Sole>; giorno: number; vista: Shaped<Vista> }
  }
}
