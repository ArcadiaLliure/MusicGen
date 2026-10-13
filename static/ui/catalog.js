// ============================================================================
// Arcàdia Lliure Studio - Catàleg d'Estils i d'Instruments Musicals (>120)
// Preserva estrictament els 23 IDs preexistents i afegeix recursos vocals,
// instruments històrics (Roma, Grècia, Bizanci, Medieval, Renaixement, Barroc),
// folk tradicional (Catalunya, Celta, Món) i orquestrals/moderns.
// ============================================================================

const STYLES = [
  { id: "all", name: "Tots els instruments", desc: "Catàleg complet d'instruments" },
  { id: "ancient_rome", name: "Antiga Roma", desc: "Música i instruments de l'antiga Roma republicana i imperial" },
  { id: "ancient_greece", name: "Antiga Grècia", desc: "Música hel·lènica clàssica i arcaica" },
  { id: "byzantine", name: "Bizantí", desc: "Tradició musical sacra i cortesana de l'Imperi Bizantí" },
  { id: "monastic_gregorian", name: "Monàstic i Cant gregorià", desc: "Música litúrgica monàstica, cants plans i gregorià" },
  { id: "medieval_european", name: "Medieval europeu", desc: "Trobadors, joglars, música cortesana i polifonia medieval" },
  { id: "medieval_fantasy", name: "Medieval fantàstic", desc: "Atmosfera medieval èpica i llegendària per a bandes sonores" },
  { id: "renaissance", name: "Renaixement", desc: "Música polifònica, madrigals i consorts del segles XV-XVI" },
  { id: "baroque", name: "Barroc", desc: "Barroc europeu, baix continu, corda i vent d'època" },
  { id: "classical", name: "Classicisme", desc: "Equilibri clàssic, quartets de corda i orquestra clàssica" },
  { id: "romanticism", name: "Romanticisme", desc: "Expressivitat, virtuosisme orquestral i piano del segle XIX" },
  { id: "orchestral", name: "Orquestral simfònic", desc: "Gran orquestra simfònica completa" },
  { id: "cinematic", name: "Cinematogràfic", desc: "Banda sonora cinemàtica, textures èpiques i híbrides" },
  { id: "celtic", name: "Celta i Nòrdic", desc: "Tradició d'Irlanda, Escòcia, Gal·les, Bretanya i Escandinàvia" },
  { id: "catalan_trad", name: "Tradicional català", desc: "Cobla, música tradicional i d'arrel catalana" },
  { id: "iberian_folk", name: "Folk ibèric", desc: "Música d'arrel ibèrica i pirinenca" },
  { id: "andalusi", name: "Andalusí", desc: "Música araboandalusí i de l'Al-Àndalus medieval" },
  { id: "traditional_arabic", name: "Àrab tradicional", desc: "Maqam tradicional del Pròxim Orient i Magrib" },
  { id: "persian", name: "Persa tradicional", desc: "Sistema Radif i tradició clàssica persa" },
  { id: "indian_classical", name: "Indi clàssic", desc: "Ragues i tals de la tradició hindustani i carnàtica" },
  { id: "chinese_trad", name: "Xinès tradicional", desc: "Música tradicional xinesa de seda i bambú" },
  { id: "japanese_trad", name: "Japonès tradicional", desc: "Gagaku, Sankyoku i tradició instrumental japonesa" },
  { id: "african_trad", name: "Tradicional africà", desc: "Tradició griot, percussió i cordes de l'Àfrica occidental" },
  { id: "latin_american", name: "Andí i Llatinoamericà", desc: "Música folklòrica andina i d'Amèrica Llatina" },
  { id: "sacred_choral", name: "Música sacra i coral", desc: "Música coral polifònica, misses i motets" },
  { id: "jazz", name: "Jazz", desc: "Swing, bebop, modal jazz i fusió" },
  { id: "blues", name: "Blues", desc: "Delta, Chicago blues i acústic" },
  { id: "rock", name: "Rock", desc: "Classic rock, hard rock i rock progressiu" },
  { id: "pop", name: "Pop", desc: "Producció pop vocal moderna" },
  { id: "electronic", name: "Electrònica", desc: "Sintetitzadors, seqüències i producció electrònica" },
  { id: "ambient", name: "Ambient", desc: "Paisatges sonors, drons i atmosferes meditatives" },
  { id: "contemporary_folk", name: "Folk contemporani", desc: "Indie folk, cantautor acústic i fusió moderna" }
];

const CATALOG_INSTRUMENTS = [
  // ==========================================
  // RECURSOS VOCALS (Master "Voice" + Cors)
  // ==========================================
  {
    id: "Voice",
    name: "Voz (Veu)",
    icon: "mdi:microphone",
    color: "%23FF1493",
    style: "transform: scale(1.15);",
    styles: ["all", "ancient_rome", "ancient_greece", "byzantine", "monastic_gregorian", "medieval_european", "medieval_fantasy", "renaissance", "baroque", "classical", "romanticism", "celtic", "catalan_trad", "iberian_folk", "andalusi", "traditional_arabic", "persian", "indian_classical", "chinese_trad", "japanese_trad", "african_trad", "latin_american", "sacred_choral", "jazz", "blues", "rock", "pop", "electronic", "contemporary_folk"],
    promptDesc: "expressive lead vocals, clear diction, evocative vocal delivery"
  },
  {
    id: "Choir", // PREEXISTENT
    name: "Cor mixt",
    icon: "lucide:mic",
    color: "black",
    style: "",
    styles: ["all", "byzantine", "monastic_gregorian", "medieval_european", "medieval_fantasy", "renaissance", "baroque", "classical", "romanticism", "orchestral", "cinematic", "sacred_choral", "pop"],
    promptDesc: "mixed choir chorus, harmonious polyphonic choral accompaniment"
  },
  {
    id: "Gregorian Chant",
    name: "Cant gregorià",
    icon: "game-icons:monk-face",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "monastic_gregorian", "medieval_european", "sacred_choral", "ambient"],
    promptDesc: "Gregorian chant, monastic Latin plainchant, resonant cathedral acoustics"
  },
  {
    id: "Byzantine Chant",
    name: "Cant bizantí",
    icon: "mdi:cross",
    color: "%23B8860B",
    style: "",
    styles: ["all", "byzantine", "sacred_choral"],
    promptDesc: "Byzantine chant, Greek microtonal liturgical vocal psalmody with ison drone"
  },
  {
    id: "Male Choir",
    name: "Cor masculí",
    icon: "mdi:account-group",
    color: "%234682B4",
    style: "",
    styles: ["all", "monastic_gregorian", "medieval_european", "cinematic", "sacred_choral", "orchestral"],
    promptDesc: "deep male choir, resonant baritone and bass voices"
  },
  {
    id: "Female Choir",
    name: "Cor femení",
    icon: "mdi:account-group-outline",
    color: "%23DA70D6",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy", "cinematic", "sacred_choral", "ambient"],
    promptDesc: "ethereal female choir, soaring soprano and alto harmonies"
  },
  {
    id: "Solo Voice",
    name: "Veu solista",
    icon: "mdi:microphone-variant",
    color: "%23E06666",
    style: "",
    styles: ["all", "ancient_greece", "medieval_european", "renaissance", "baroque", "celtic", "catalan_trad", "jazz", "blues", "contemporary_folk"],
    promptDesc: "intimate solo voice, delicate acoustic vocal tone"
  },

  // ==========================================
  // ELS 23 INSTRUMENTS ORIGINALS (PREEXISTENTS)
  // ==========================================
  {
    id: "Piano", // PREEXISTENT
    name: "Piano",
    icon: "mdi:piano",
    color: "black",
    style: "",
    styles: ["all", "classical", "romanticism", "orchestral", "cinematic", "jazz", "blues", "rock", "pop", "contemporary_folk"],
    promptDesc: "acoustic grand piano, rich dynamic timbre"
  },
  {
    id: "Clavicord", // PREEXISTENT
    name: "Clavicordi",
    icon: "mdi:piano",
    color: "%238B4513",
    style: "transform: scaleX(-1);",
    styles: ["all", "renaissance", "baroque", "classical"],
    promptDesc: "clavichord, intimate expressive keyboard with subtle vibrato"
  },
  {
    id: "Synth", // PREEXISTENT
    name: "Sintetitzador",
    icon: "game-icons:piano-keys",
    color: "%239400D3",
    style: "",
    styles: ["all", "electronic", "pop", "rock", "ambient", "cinematic"],
    promptDesc: "analog synthesizer pads, leads and arpeggios"
  },
  {
    id: "Acoustic Guitar", // PREEXISTENT
    name: "Guitarra acústica",
    icon: "mdi:guitar-acoustic",
    color: "%23D2691E",
    style: "",
    styles: ["all", "celtic", "contemporary_folk", "pop", "rock", "blues"],
    promptDesc: "acoustic steel-string guitar, warm fingerpicked and strummed tone"
  },
  {
    id: "Spanish Guitar", // PREEXISTENT
    name: "Guitarra espanyola",
    icon: "mdi:guitar-acoustic",
    color: "%238B0000",
    style: "transform: rotate(15deg);",
    styles: ["all", "catalan_trad", "iberian_folk", "andalusi", "classical", "romanticism", "contemporary_folk"],
    promptDesc: "Spanish classical nylon-string guitar, resonant rasgueados and arpeggios"
  },
  {
    id: "Elec Guitar", // PREEXISTENT
    name: "Guitarra elèctrica",
    icon: "mdi:guitar-electric",
    color: "%231E90FF",
    style: "",
    styles: ["all", "rock", "blues", "pop", "jazz"],
    promptDesc: "electric guitar, clean and overdriven melodic tones"
  },
  {
    id: "Bass", // PREEXISTENT
    name: "Baix elèctric",
    icon: "mdi:guitar-electric",
    color: "%2332CD32",
    style: "transform: scale(1.1) rotate(-10deg);",
    styles: ["all", "rock", "pop", "jazz", "blues", "electronic"],
    promptDesc: "electric bass guitar, deep grooving bassline"
  },
  {
    id: "Ukulele", // PREEXISTENT
    name: "Ukelele",
    icon: "qlementine-icons:ukulele-24",
    color: "%23DEB887",
    style: "",
    styles: ["all", "pop", "contemporary_folk"],
    promptDesc: "acoustic ukulele, bright cheerful strumming"
  },
  {
    id: "Harp", // PREEXISTENT
    name: "Arpa",
    icon: "game-icons:harp",
    color: "%23DAA520",
    style: "",
    styles: ["all", "medieval_fantasy", "renaissance", "baroque", "classical", "romanticism", "orchestral", "cinematic", "celtic"],
    promptDesc: "concert pedal harp, delicate cascading arpeggios and glissandos"
  },
  {
    id: "Contrabass", // PREEXISTENT
    name: "Contrabaix",
    icon: "qlementine-icons:cello-24",
    color: "%235C4033",
    style: "transform: scale(1.3);",
    styles: ["all", "classical", "romanticism", "orchestral", "cinematic", "jazz"],
    promptDesc: "acoustic double bass, bowed orchestral contrabass and pizzicato jazz bass"
  },
  {
    id: "Cello", // PREEXISTENT
    name: "Violoncel",
    icon: "qlementine-icons:cello-24",
    color: "%238B4513",
    style: "",
    styles: ["all", "baroque", "classical", "romanticism", "orchestral", "cinematic", "contemporary_folk"],
    promptDesc: "cello, deep emotional bowed cello melodies"
  },
  {
    id: "Violin", // PREEXISTENT
    name: "Violí",
    icon: "mdi:violin",
    color: "%23A0522D",
    style: "",
    styles: ["all", "baroque", "classical", "romanticism", "orchestral", "cinematic", "celtic", "catalan_trad", "contemporary_folk"],
    promptDesc: "violin, sweet and virtuosic acoustic violin tone"
  },
  {
    id: "Flute", // PREEXISTENT
    name: "Flauta travessera",
    icon: "game-icons:flute",
    color: "%23708090",
    style: "",
    styles: ["all", "baroque", "classical", "romanticism", "orchestral", "cinematic", "celtic", "contemporary_folk"],
    promptDesc: "concert western flute, airy and agile melodic woodwind"
  },
  {
    id: "Clarinet", // PREEXISTENT
    name: "Clarinet",
    icon: "game-icons:clarinet",
    color: "black",
    style: "",
    styles: ["all", "classical", "romanticism", "orchestral", "cinematic", "jazz", "catalan_trad"],
    promptDesc: "acoustic clarinet, smooth and expressive wooden timbre"
  },
  {
    id: "Oboe", // PREEXISTENT
    name: "Oboè",
    icon: "game-icons:clarinet",
    color: "%232F4F4F",
    style: "transform: scaleY(-1);",
    styles: ["all", "baroque", "classical", "romanticism", "orchestral", "cinematic"],
    promptDesc: "acoustic oboe, poignant double-reed melodic tone"
  },
  {
    id: "Fagot", // PREEXISTENT
    name: "Fagot",
    icon: "game-icons:bassoon",
    color: "%238B4513",
    style: "",
    styles: ["all", "baroque", "classical", "romanticism", "orchestral", "cinematic"],
    promptDesc: "orchestral bassoon, warm woody low double-reed register"
  },
  {
    id: "Gralla", // PREEXISTENT
    name: "Gralla",
    icon: "game-icons:clarinet",
    color: "%23CD853F",
    style: "",
    styles: ["all", "catalan_trad", "iberian_folk", "medieval_european"],
    promptDesc: "Catalan gralla, powerful piercing traditional double reed shawm"
  },
  {
    id: "Saxophone", // PREEXISTENT
    name: "Saxòfon",
    icon: "mdi:saxophone",
    color: "%23DAA520",
    style: "",
    styles: ["all", "jazz", "blues", "rock", "pop"],
    promptDesc: "saxophone, expressive brassy reedy tone"
  },
  {
    id: "Trumpet", // PREEXISTENT
    name: "Trompeta",
    icon: "mdi:trumpet",
    color: "%23FFA500",
    style: "",
    styles: ["all", "classical", "romanticism", "orchestral", "cinematic", "jazz", "catalan_trad"],
    promptDesc: "trumpet, bright triumphant brass melody"
  },
  {
    id: "Trombone", // PREEXISTENT
    name: "Trombó",
    icon: "game-icons:trombone",
    color: "%23DAA520",
    style: "",
    styles: ["all", "classical", "romanticism", "orchestral", "cinematic", "jazz"],
    promptDesc: "tenor trombone, warm and majestic brass slide"
  },
  {
    id: "Harmonica", // PREEXISTENT
    name: "Harmònica",
    icon: "qlementine-icons:harmonica-16",
    color: "%234682B4",
    style: "transform: scale(1.3);",
    styles: ["all", "blues", "contemporary_folk", "rock"],
    promptDesc: "blues harmonica, soulful acoustic reed bends"
  },
  {
    id: "Drums", // PREEXISTENT
    name: "Bateria",
    icon: "lucide:drum",
    color: "%23FF4500",
    style: "",
    styles: ["all", "rock", "pop", "jazz", "blues"],
    promptDesc: "full acoustic drum kit, kick, snare, hi-hat and cymbals groove"
  },

  // ==========================================
  // ANTIGA ROMA
  // ==========================================
  {
    id: "Roman Tibia",
    name: "Tibia romana",
    icon: "game-icons:flute",
    color: "%238B0000",
    style: "",
    styles: ["all", "ancient_rome"],
    promptDesc: "ancient Roman tibia, twin reeded pipes with piercing archaic timbre"
  },
  {
    id: "Roman Lyre",
    name: "Lira romana",
    icon: "game-icons:harp",
    color: "%23CD853F",
    style: "transform: scale(0.9);",
    styles: ["all", "ancient_rome"],
    promptDesc: "ancient Roman lyra, plucked gut strings with wooden soundbox"
  },
  {
    id: "Roman Kithara",
    name: "Cítara romana",
    icon: "game-icons:harp",
    color: "%23DAA520",
    style: "transform: scale(1.1);",
    styles: ["all", "ancient_rome"],
    promptDesc: "Roman kithara, concert wooden stringed instrument with resonant box"
  },
  {
    id: "Cornu",
    name: "Cornu",
    icon: "game-icons:hunting-horn",
    color: "%23B8860B",
    style: "transform: scale(1.2);",
    styles: ["all", "ancient_rome", "cinematic"],
    promptDesc: "Roman cornu, large circular bronze military horn with crossbar"
  },
  {
    id: "Buccina",
    name: "Bucina",
    icon: "game-icons:hunting-horn",
    color: "%23CC7722",
    style: "",
    styles: ["all", "ancient_rome"],
    promptDesc: "ancient Roman buccina, curved brass military horn"
  },
  {
    id: "Roman Tuba",
    name: "Tuba romana",
    icon: "mdi:trumpet",
    color: "%23A0522D",
    style: "",
    styles: ["all", "ancient_rome"],
    promptDesc: "Roman straight military brass tuba, direct solemn trumpet call"
  },
  {
    id: "Lituus",
    name: "Lituus",
    icon: "game-icons:horn-internal",
    color: "%238B4513",
    style: "",
    styles: ["all", "ancient_rome"],
    promptDesc: "Roman lituus, long straight bronze horn with upturned flared bell"
  },
  {
    id: "Hydraulis",
    name: "Hydraulis (Òrgan hidràulic)",
    icon: "game-icons:pipe-organ",
    color: "%234682B4",
    style: "",
    styles: ["all", "ancient_rome", "ancient_greece", "byzantine"],
    promptDesc: "ancient Roman water organ hydraulis, clear fluty organ pipes driven by water pressure"
  },
  {
    id: "Sistrum",
    name: "Sistro",
    icon: "game-icons:shaking-hands",
    color: "%23FFD700",
    style: "",
    styles: ["all", "ancient_rome", "ancient_greece"],
    promptDesc: "ancient bronze sistrum, shimmering metallic ritual rattle"
  },
  {
    id: "Ancient Cymbals",
    name: "Címbals antics",
    icon: "lucide:drum",
    color: "%23DAA520",
    style: "",
    styles: ["all", "ancient_rome", "ancient_greece", "byzantine"],
    promptDesc: "ancient bronze finger cymbals, bright metallic ringing resonance"
  },
  {
    id: "Crotales",
    name: "Cròtals",
    icon: "game-icons:tambourine",
    color: "%23B8860B",
    style: "",
    styles: ["all", "ancient_rome", "ancient_greece"],
    promptDesc: "ancient wooden and bronze crotales clappers, rhythmic accent percussion"
  },
  {
    id: "Scabellum",
    name: "Scabellum",
    icon: "game-icons:foot-trip",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "ancient_rome"],
    promptDesc: "Roman scabellum wooden foot clapper, prominent rhythmic theatrical pulse"
  },
  {
    id: "Pan Flute",
    name: "Siringa (Flauta de Pan)",
    icon: "game-icons:pan-flute",
    color: "%23DEB887",
    style: "",
    styles: ["all", "ancient_rome", "ancient_greece", "latin_american", "contemporary_folk"],
    promptDesc: "pan flute syrinx, multi-tubed breathy melodic pipes"
  },
  {
    id: "Pandura",
    name: "Pandura",
    icon: "mdi:guitar-acoustic",
    color: "%23CD853F",
    style: "",
    styles: ["all", "ancient_rome", "ancient_greece", "byzantine"],
    promptDesc: "ancient long-necked plucked lute pandura, crisp antique string tone"
  },
  {
    id: "Roman Tympanum",
    name: "Tímpan romà",
    icon: "game-icons:drum",
    color: "%23A0522D",
    style: "",
    styles: ["all", "ancient_rome"],
    promptDesc: "ancient Roman tympanum hand drum, deep animal skin percussion"
  },

  // ==========================================
  // ANTIGA GRÈCIA
  // ==========================================
  {
    id: "Greek Kithara",
    name: "Cítara grega",
    icon: "game-icons:harp",
    color: "%23C5A059",
    style: "",
    styles: ["all", "ancient_greece"],
    promptDesc: "ancient Greek kithara, noble ceremonial plucked lyre"
  },
  {
    id: "Greek Lyre",
    name: "Lira grega (Khélis)",
    icon: "game-icons:harp",
    color: "%23A0522D",
    style: "transform: scale(0.85);",
    styles: ["all", "ancient_greece"],
    promptDesc: "ancient Greek tortoise-shell lyre, sweet gentle plucked melody"
  },
  {
    id: "Greek Aulos",
    name: "Aulos grec",
    icon: "game-icons:flute",
    color: "%23556B2F",
    style: "",
    styles: ["all", "ancient_greece"],
    promptDesc: "ancient Greek double-reed aulos pipes, intense modal microtonal melody"
  },
  {
    id: "Barbitos",
    name: "Bàrbiton",
    icon: "game-icons:harp",
    color: "%238B4513",
    style: "transform: scaleY(1.2);",
    styles: ["all", "ancient_greece"],
    promptDesc: "ancient Greek barbitos, long-armed bass lyre with deep sonorous strings"
  },
  {
    id: "Phorminx",
    name: "Forminx",
    icon: "game-icons:harp",
    color: "%23D2691E",
    style: "",
    styles: ["all", "ancient_greece"],
    promptDesc: "Homeric phorminx, archaic seven-stringed crescent lyre"
  },
  {
    id: "Salpinx",
    name: "Sàlpinx",
    icon: "mdi:trumpet",
    color: "%23CD7F32",
    style: "",
    styles: ["all", "ancient_greece"],
    promptDesc: "ancient Greek straight bronze trumpet salpinx, commanding heraldic tone"
  },
  {
    id: "Greek Tympanon",
    name: "Tímpanon grec",
    icon: "game-icons:drum",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "ancient_greece"],
    promptDesc: "ancient Greek frame drum tympanon, resonant Dionysian percussion"
  },

  // ==========================================
  // BIZANCI
  // ==========================================
  {
    id: "Byzantine Lyra",
    name: "Lira bizantina",
    icon: "mdi:violin",
    color: "%23DAA520",
    style: "",
    styles: ["all", "byzantine", "medieval_european"],
    promptDesc: "Byzantine pear-shaped bowed lyra, precursor to European fiddle with warm drone"
  },
  {
    id: "Byzantine Psaltery",
    name: "Salteri bizantí",
    icon: "game-icons:harp",
    color: "%23CD853F",
    style: "",
    styles: ["all", "byzantine"],
    promptDesc: "Byzantine canon/psaltery, plucked metallic zither strings"
  },
  {
    id: "Liturgical Bells",
    name: "Campanes litúrgiques",
    icon: "game-icons:church",
    color: "%23FFD700",
    style: "",
    styles: ["all", "byzantine", "monastic_gregorian", "sacred_choral"],
    promptDesc: "Eastern Orthodox church bells, rich harmonic peals and chime resonances"
  },
  {
    id: "Byzantine Organ",
    name: "Òrgan bizantí imperial",
    icon: "game-icons:pipe-organ",
    color: "%23B8860B",
    style: "",
    styles: ["all", "byzantine"],
    promptDesc: "Byzantine court pneumatic pipe organ, bright solemn ceremonial timbre"
  },
  {
    id: "Def",
    name: "Def (Pander bizantí)",
    icon: "game-icons:tambourine",
    color: "%238B4513",
    style: "",
    styles: ["all", "byzantine", "traditional_arabic"],
    promptDesc: "def frame drum with bronze jingles, crisp rhythmic driving pulse"
  },

  // ==========================================
  // MEDIEVAL EUROPEU I FANTÀSTIC
  // ==========================================
  {
    id: "Medieval Lute",
    name: "Llaüt medieval",
    icon: "mdi:guitar-acoustic",
    color: "%238B4513",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy", "renaissance"],
    promptDesc: "medieval plectrum lute, gut strings with bright articulate pluck"
  },
  {
    id: "Medieval Vihuela",
    name: "Vihuela medieval",
    icon: "mdi:guitar-acoustic",
    color: "%23CD853F",
    style: "",
    styles: ["all", "medieval_european", "iberian_folk", "renaissance"],
    promptDesc: "medieval bowed and plucked vihuela de mano, rich historical timbre"
  },
  {
    id: "Gittern",
    name: "Guiterna",
    icon: "mdi:guitar-acoustic",
    color: "%23A0522D",
    style: "transform: scale(0.9);",
    styles: ["all", "medieval_european"],
    promptDesc: "medieval gittern, small carved wooden lute with quill plectrum"
  },
  {
    id: "Citole",
    name: "Cítola",
    icon: "mdi:guitar-acoustic",
    color: "%23B8860B",
    style: "",
    styles: ["all", "medieval_european"],
    promptDesc: "medieval citole, trefoil-shaped plucked string instrument"
  },
  {
    id: "Medieval Harp",
    name: "Arpa medieval",
    icon: "game-icons:harp",
    color: "%23C5A059",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy", "celtic"],
    promptDesc: "gothic medieval harp with bray pins, buzzing crystalline timbre"
  },
  {
    id: "Medieval Psaltery",
    name: "Salteri medieval",
    icon: "game-icons:harp",
    color: "%23DAA520",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy"],
    promptDesc: "pig's head medieval psaltery, clear bell-like plucked zither"
  },
  {
    id: "Rebec",
    name: "Rabel",
    icon: "mdi:violin",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "medieval_european", "iberian_folk"],
    promptDesc: "medieval rebec, bowed three-string wooden instrument with sharp piercing voice"
  },
  {
    id: "Vielle",
    name: "Fídula (Vielle)",
    icon: "mdi:violin",
    color: "%238B4513",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy"],
    promptDesc: "medieval fiddle vielle, oval bowed instrument with drone strings"
  },
  {
    id: "Organistrum",
    name: "Organistre",
    icon: "mdi:violin",
    color: "%235C4033",
    style: "",
    styles: ["all", "medieval_european"],
    promptDesc: "two-player medieval organistrum, large continuous drone wheel instrument"
  },
  {
    id: "Hurdy-gurdy",
    name: "Zanfona (Viola de roda)",
    icon: "mdi:violin",
    color: "%238B4513",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy", "celtic", "iberian_folk", "contemporary_folk"],
    promptDesc: "hurdy-gurdy zanfona, continuous buzzing drone wheel and keyed melodic strings"
  },
  {
    id: "Portative Organ",
    name: "Òrgan portatiu",
    icon: "game-icons:pipe-organ",
    color: "%234682B4",
    style: "",
    styles: ["all", "medieval_european"],
    promptDesc: "medieval portative organetto, handheld pipes with bellows"
  },
  {
    id: "Positive Organ",
    name: "Òrgan positiu",
    icon: "game-icons:pipe-organ",
    color: "%232F4F4F",
    style: "",
    styles: ["all", "medieval_european", "renaissance", "baroque"],
    promptDesc: "chamber positive organ, warm flute and principal wooden pipe stops"
  },
  {
    id: "Medieval Recorder",
    name: "Flauta de bec medieval",
    icon: "game-icons:flute",
    color: "%23A0522D",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy"],
    promptDesc: "medieval cylindrical wooden recorder, pure hollow breathy melody"
  },
  {
    id: "Pipe and Tabor",
    name: "Flauta i tamboril",
    icon: "game-icons:flute",
    color: "%23CD853F",
    style: "",
    styles: ["all", "medieval_european", "catalan_trad", "iberian_folk"],
    promptDesc: "three-hole pipe and tabor drum played simultaneously by one musician"
  },
  {
    id: "Shawm",
    name: "Chirimía (Xirimia)",
    icon: "game-icons:clarinet",
    color: "%238B0000",
    style: "",
    styles: ["all", "medieval_european", "renaissance"],
    promptDesc: "medieval shawm, outdoor double-reed woodwind with fiery loud tone"
  },
  {
    id: "Bombard",
    name: "Bombarda",
    icon: "game-icons:clarinet",
    color: "%234A2E12",
    style: "",
    styles: ["all", "medieval_european", "celtic"],
    promptDesc: "Breton and medieval bombard, powerful piercing low-pitch double reed"
  },
  {
    id: "Medieval Bagpipe",
    name: "Cornamusa medieval",
    icon: "game-icons:bagpipes",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy"],
    promptDesc: "medieval drone bagpipe, leather bag with cane chanter and bass drone"
  },
  {
    id: "Anafil",
    name: "Añafil",
    icon: "mdi:trumpet",
    color: "%23DAA520",
    style: "",
    styles: ["all", "medieval_european", "andalusi"],
    promptDesc: "straight Moorish and medieval brass trumpet anafil, fanfare signals"
  },
  {
    id: "Natural Horn",
    name: "Corn natural (Banya)",
    icon: "game-icons:hunting-horn",
    color: "%23654321",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy"],
    promptDesc: "animal horn and medieval hunting horn, rustic resonant call"
  },
  {
    id: "Tabor",
    name: "Atabal medieval",
    icon: "game-icons:drum",
    color: "%238B4513",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy"],
    promptDesc: "medieval tabor rope-tension drum with snare gut string"
  },
  {
    id: "Nakers",
    name: "Nacaris (Nakers)",
    icon: "game-icons:drum",
    color: "%23CD853F",
    style: "",
    styles: ["all", "medieval_european"],
    promptDesc: "medieval paired kettle drums nakers, sharp rhythmic percussive strikes"
  },
  {
    id: "Medieval Chimes",
    name: "Campanetes medievals",
    icon: "game-icons:church",
    color: "%23FFD700",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy", "sacred_choral"],
    promptDesc: "medieval chime bells tintinnabulum, delicate high metallic ringing"
  },
  {
    id: "Dulcimer",
    name: "Salteri percutit (Dulcimer)",
    icon: "game-icons:harp",
    color: "%23B8860B",
    style: "",
    styles: ["all", "medieval_european", "medieval_fantasy", "contemporary_folk"],
    promptDesc: "hammered dulcimer, wooden mallets striking brass strings with sustained sparkle"
  },

  // ==========================================
  // RENAIXEMENT I BARROC
  // ==========================================
  {
    id: "Harpsichord",
    name: "Clavicèmbal (Clavecí)",
    icon: "mdi:piano",
    color: "%23DAA520",
    style: "transform: scale(0.95);",
    styles: ["all", "renaissance", "baroque"],
    promptDesc: "two-manual baroque harpsichord, bright plucking quill keyboard counterpoint"
  },
  {
    id: "Virginal",
    name: "Virginal",
    icon: "mdi:piano",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "renaissance"],
    promptDesc: "renaissance virginal keyboard, sweet resonant plucked box timbre"
  },
  {
    id: "Theorbo",
    name: "Tiorba",
    icon: "mdi:guitar-acoustic",
    color: "%235C4033",
    style: "transform: scaleY(1.3);",
    styles: ["all", "baroque"],
    promptDesc: "theorbo extended-neck archlute, deep diapason bass gut strings for basso continuo"
  },
  {
    id: "Viola da Gamba",
    name: "Viola da gamba",
    icon: "qlementine-icons:cello-24",
    color: "%23A0522D",
    style: "",
    styles: ["all", "renaissance", "baroque"],
    promptDesc: "six-string fretted viola da gamba, warm silvery bowed consort tone"
  },
  {
    id: "Cornett",
    name: "Cornetto (Zink)",
    icon: "game-icons:hunting-horn",
    color: "%232F4F4F",
    style: "",
    styles: ["all", "renaissance", "baroque"],
    promptDesc: "leather-wrapped wooden cornett zink with trumpet mouthpiece, singing human-like brass tone"
  },
  {
    id: "Sackbut",
    name: "Sacabutx",
    icon: "game-icons:trombone",
    color: "%23B8860B",
    style: "",
    styles: ["all", "renaissance", "baroque"],
    promptDesc: "renaissance sackbut early trombone, soft mellow blendable brass slide"
  },
  {
    id: "Crumhorn",
    name: "Cromorn",
    icon: "game-icons:clarinet",
    color: "%238B4513",
    style: "",
    styles: ["all", "renaissance"],
    promptDesc: "capped reed crumhorn, buzzy nasal wooden consort wind"
  },
  {
    id: "Dulcian",
    name: "Dulcià",
    icon: "game-icons:bassoon",
    color: "%23654321",
    style: "",
    styles: ["all", "renaissance", "baroque"],
    promptDesc: "renaissance dulcian proto-bassoon, warm soft wooden low double reed"
  },
  {
    id: "Baroque Organ",
    name: "Òrgan barroc",
    icon: "game-icons:pipe-organ",
    color: "%23B8860B",
    style: "",
    styles: ["all", "baroque", "sacred_choral"],
    promptDesc: "North German baroque pipe organ, grand polyphonic mixture and reed stops"
  },
  {
    id: "Natural Trumpet",
    name: "Trompeta natural barroca",
    icon: "mdi:trumpet",
    color: "%23FFD700",
    style: "",
    styles: ["all", "baroque"],
    promptDesc: "valveless baroque natural trumpet, clarino high-register festive brass"
  },

  // ==========================================
  // TRADICIONAL CATALÀ I FOLK IBÈRIC
  // ==========================================
  {
    id: "Tenora",
    name: "Tenora",
    icon: "game-icons:clarinet",
    color: "%238B4513",
    style: "transform: scale(1.15);",
    styles: ["all", "catalan_trad"],
    promptDesc: "Catalan tenora cobla oboe, majestic resonant metallic-belled double reed"
  },
  {
    id: "Tible",
    name: "Tible",
    icon: "game-icons:clarinet",
    color: "%23CD853F",
    style: "transform: scale(0.9);",
    styles: ["all", "catalan_trad"],
    promptDesc: "Catalan tible treble shawm, bright agile festive melody"
  },
  {
    id: "Flabiol",
    name: "Flabiol i tamborí",
    icon: "game-icons:flute",
    color: "%23A0522D",
    style: "",
    styles: ["all", "catalan_trad"],
    promptDesc: "Catalan flabiol one-handed whistle and tamborí side drum"
  },
  {
    id: "Sac de Gemecs",
    name: "Sac de gemecs",
    icon: "game-icons:bagpipes",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "catalan_trad"],
    promptDesc: "Catalan sac de gemecs bagpipe with three hanging bass drones"
  },
  {
    id: "Xeremia",
    name: "Xeremia mallorquina",
    icon: "game-icons:bagpipes",
    color: "%23B8860B",
    style: "",
    styles: ["all", "catalan_trad", "iberian_folk"],
    promptDesc: "Majorcan xeremia bagpipe, lively traditional Mediterranean dance tone"
  },
  {
    id: "Dolsaina",
    name: "Dolçaina",
    icon: "game-icons:clarinet",
    color: "%23D2691E",
    style: "",
    styles: ["all", "catalan_trad", "iberian_folk"],
    promptDesc: "Valencian dolçaina traditional shawm, intense penetrating festival melody"
  },
  {
    id: "Tarota",
    name: "Tarota",
    icon: "game-icons:clarinet",
    color: "%235C4033",
    style: "",
    styles: ["all", "catalan_trad", "medieval_european"],
    promptDesc: "wooden rustic tarota shawm, deep archaic double reed timbre"
  },
  {
    id: "Alboka",
    name: "Alboka",
    icon: "game-icons:hunting-horn",
    color: "%23DAA520",
    style: "",
    styles: ["all", "iberian_folk"],
    promptDesc: "Basque alboka double hornpipe, continuous circular-breathed reed drone"
  },
  {
    id: "Txistu",
    name: "Txistu",
    icon: "game-icons:flute",
    color: "%234682B4",
    style: "",
    styles: ["all", "iberian_folk"],
    promptDesc: "Basque txistu three-hole pipe, agile high folk flute melody"
  },
  {
    id: "Trikitixa",
    name: "Trikitixa",
    icon: "game-icons:piano-keys",
    color: "%23B22222",
    style: "",
    styles: ["all", "iberian_folk"],
    promptDesc: "diatonic button accordion trikitixa, energetic upbeat folk rhythms"
  },
  {
    id: "Gaita Gallega",
    name: "Gaita gallega",
    icon: "game-icons:bagpipes",
    color: "%234169E1",
    style: "",
    styles: ["all", "iberian_folk", "celtic"],
    promptDesc: "Galician gaita bagpipe, rich harmonic drone and lyrical folk ornamentation"
  },
  {
    id: "Gaita Asturiana",
    name: "Gaita asturiana",
    icon: "game-icons:bagpipes",
    color: "%2332CD32",
    style: "",
    styles: ["all", "iberian_folk", "celtic"],
    promptDesc: "Asturian gaita bagpipe, powerful loud tonic drone and bright chanter"
  },

  // ==========================================
  // CELTA I NÒRDIC
  // ==========================================
  {
    id: "Bodhran",
    name: "Bodhrán",
    icon: "game-icons:drum",
    color: "%238B4513",
    style: "",
    styles: ["all", "celtic"],
    promptDesc: "Irish bodhrán frame drum, tipper-struck rhythmic pulse with pitch inflection"
  },
  {
    id: "Tin Whistle",
    name: "Tin whistle",
    icon: "game-icons:flute",
    color: "%23C0C0C0",
    style: "",
    styles: ["all", "celtic", "contemporary_folk"],
    promptDesc: "Irish tin penny whistle, sweet airy rapid ornamentations and jigs"
  },
  {
    id: "Low Whistle",
    name: "Low whistle",
    icon: "game-icons:flute",
    color: "%232F4F4F",
    style: "transform: scale(1.2);",
    styles: ["all", "celtic", "cinematic", "ambient"],
    promptDesc: "low D Irish whistle, deep haunting breathy cinematic air"
  },
  {
    id: "Uilleann Pipes",
    name: "Uilleann pipes",
    icon: "game-icons:bagpipes",
    color: "%23228B22",
    style: "",
    styles: ["all", "celtic"],
    promptDesc: "Irish uilleann pipes, bellows-blown bagpipe with chanter, regulators and drones"
  },
  {
    id: "Irish Bouzouki",
    name: "Bouzouki irlandès",
    icon: "mdi:guitar-acoustic",
    color: "%23CD853F",
    style: "",
    styles: ["all", "celtic", "contemporary_folk"],
    promptDesc: "Irish bouzouki, eight-string ringing open-chord accompaniment"
  },
  {
    id: "Nyckelharpa",
    name: "Nyckelharpa",
    icon: "mdi:violin",
    color: "%23A0522D",
    style: "",
    styles: ["all", "celtic", "medieval_fantasy", "contemporary_folk"],
    promptDesc: "Swedish nyckelharpa keyed fiddle, sympathetic strings creating shimmering resonance"
  },
  {
    id: "Hardanger Fiddle",
    name: "Hardanger fiddle (Hardingfele)",
    icon: "mdi:violin",
    color: "%23DAA520",
    style: "",
    styles: ["all", "celtic", "contemporary_folk"],
    promptDesc: "Norwegian Hardanger fiddle, decorated folk violin with sympathetic resonant strings"
  },
  {
    id: "Kantele",
    name: "Kantele",
    icon: "game-icons:harp",
    color: "%23B8860B",
    style: "",
    styles: ["all", "celtic", "ambient"],
    promptDesc: "Finnish plucked kantele zither, bell-like pure acoustic resonance"
  },

  // ==========================================
  // ORIENT PRÒXIM, ÀRAB I PERSA
  // ==========================================
  {
    id: "Oud",
    name: "Oud (Laüt àrab)",
    icon: "mdi:guitar-acoustic",
    color: "%238B4513",
    style: "",
    styles: ["all", "andalusi", "traditional_arabic", "persian"],
    promptDesc: "fretless wooden oud, deep microtonal ornamentation and resonant warm plucking"
  },
  {
    id: "Qanun",
    name: "Qanun",
    icon: "game-icons:harp",
    color: "%23DAA520",
    style: "",
    styles: ["all", "andalusi", "traditional_arabic", "persian"],
    promptDesc: "Middle Eastern qanun zither, metallic plucked mandals with rapid tremolos"
  },
  {
    id: "Ney",
    name: "Ney",
    icon: "game-icons:flute",
    color: "%23C5A059",
    style: "",
    styles: ["all", "traditional_arabic", "persian", "andalusi", "ambient"],
    promptDesc: "end-blown reed flute ney, breathy meditative Sufi microtonal melodies"
  },
  {
    id: "Duduk",
    name: "Duduk",
    icon: "game-icons:flute",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "persian", "traditional_arabic", "cinematic", "ambient"],
    promptDesc: "Armenian apricot-wood duduk double-reed flute, deeply mournful warm soul timbre"
  },
  {
    id: "Zurna",
    name: "Zurna",
    icon: "game-icons:clarinet",
    color: "%23B22222",
    style: "",
    styles: ["all", "traditional_arabic", "persian"],
    promptDesc: "zurna outdoor double reed, fiery loud celebratory folk tone"
  },
  {
    id: "Saz",
    name: "Saz (Bağlama)",
    icon: "mdi:guitar-acoustic",
    color: "%23CD853F",
    style: "transform: scaleY(1.2);",
    styles: ["all", "traditional_arabic", "persian", "contemporary_folk"],
    promptDesc: "long-necked saz baglama, tied microtonal frets and shimmering drone strings"
  },
  {
    id: "Santur",
    name: "Santur persa",
    icon: "game-icons:harp",
    color: "%23D2691E",
    style: "",
    styles: ["all", "persian", "indian_classical"],
    promptDesc: "Persian hammered santur, delicate mesrap strikes creating glittering metallic sustained tones"
  },
  {
    id: "Kamancheh",
    name: "Kamancheh",
    icon: "mdi:violin",
    color: "%234A2E12",
    style: "",
    styles: ["all", "persian", "traditional_arabic"],
    promptDesc: "Persian bowed spike fiddle kamancheh, silky microtonal melody"
  },
  {
    id: "Darbuka",
    name: "Darbuka",
    icon: "game-icons:drum",
    color: "%23708090",
    style: "",
    styles: ["all", "traditional_arabic", "andalusi", "persian"],
    promptDesc: "goblet darbuka doumbek drum, sharp doum bass and tak rim accents"
  },
  {
    id: "Riq",
    name: "Riq (Pandereta àrab)",
    icon: "game-icons:tambourine",
    color: "%23DAA520",
    style: "",
    styles: ["all", "traditional_arabic", "andalusi"],
    promptDesc: "Arabic riq tambourine with heavy brass jingles, virtuosic rhythmic finger rolls"
  },
  {
    id: "Bendir",
    name: "Bendir",
    icon: "game-icons:drum",
    color: "%238B4513",
    style: "",
    styles: ["all", "traditional_arabic", "andalusi", "monastic_gregorian"],
    promptDesc: "North African bendir frame drum with snare cords, deep buzzing ritual resonance"
  },

  // ==========================================
  // ÍNDIA I ÀSIA ORIENTAL
  // ==========================================
  {
    id: "Sitar",
    name: "Sitar",
    icon: "mdi:guitar-acoustic",
    color: "%23FF8C00",
    style: "transform: scale(1.15);",
    styles: ["all", "indian_classical", "ambient"],
    promptDesc: "Indian classical sitar, jawari buzzing bridge and meend note bends with sympathetic tarabs"
  },
  {
    id: "Sarod",
    name: "Sarod",
    icon: "mdi:guitar-acoustic",
    color: "%238B4513",
    style: "",
    styles: ["all", "indian_classical"],
    promptDesc: "fretless steel-fingerboard sarod, percussive coconut plectrum and glissandos"
  },
  {
    id: "Tanpura",
    name: "Tanpura",
    icon: "mdi:guitar-acoustic",
    color: "%23DAA520",
    style: "transform: scaleY(1.2);",
    styles: ["all", "indian_classical", "ambient"],
    promptDesc: "Indian tanpura drone, continuous hypnotic acoustic overtone foundation"
  },
  {
    id: "Bansuri",
    name: "Bansuri",
    icon: "game-icons:flute",
    color: "%23CD853F",
    style: "",
    styles: ["all", "indian_classical", "ambient"],
    promptDesc: "Indian bamboo bansuri flute, lyrical glides and warm spiritual melodies"
  },
  {
    id: "Tabla",
    name: "Tabla",
    icon: "game-icons:drum",
    color: "%235C4033",
    style: "",
    styles: ["all", "indian_classical"],
    promptDesc: "paired Indian tabla drums, daya ring and baya bass pitch modulations"
  },
  {
    id: "Sarangi",
    name: "Sarangi",
    icon: "mdi:violin",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "indian_classical"],
    promptDesc: "Indian bowed sarangi, vocal-like sliding melodies through dozens of sympathetic strings"
  },
  {
    id: "Erhu",
    name: "Erhu",
    icon: "mdi:violin",
    color: "%23B22222",
    style: "",
    styles: ["all", "chinese_trad", "cinematic"],
    promptDesc: "Chinese two-string bowed erhu, deeply expressive crying vibrato"
  },
  {
    id: "Pipa",
    name: "Pipa",
    icon: "mdi:guitar-acoustic",
    color: "%23C5A059",
    style: "",
    styles: ["all", "chinese_trad"],
    promptDesc: "Chinese four-string pear-shaped pipa lute, rapid finger rolls and percussive drama"
  },
  {
    id: "Guzheng",
    name: "Guzheng",
    icon: "game-icons:harp",
    color: "%23DAA520",
    style: "",
    styles: ["all", "chinese_trad", "ambient"],
    promptDesc: "Chinese 21-string plucked guzheng zither, cascading water-like glissandos and pitch bends"
  },
  {
    id: "Dizi",
    name: "Dizi",
    icon: "game-icons:flute",
    color: "%232E8B57",
    style: "",
    styles: ["all", "chinese_trad"],
    promptDesc: "Chinese transverse bamboo dizi flute with dimo buzzing reed membrane"
  },
  {
    id: "Koto",
    name: "Koto",
    icon: "game-icons:harp",
    color: "%23D2691E",
    style: "",
    styles: ["all", "japanese_trad", "ambient"],
    promptDesc: "Japanese 13-string koto zither, elegant traditional pentatonic plucked phrases"
  },
  {
    id: "Shakuhachi",
    name: "Shakuhachi",
    icon: "game-icons:flute",
    color: "%234A2E12",
    style: "",
    styles: ["all", "japanese_trad", "ambient", "cinematic"],
    promptDesc: "Japanese end-blown bamboo shakuhachi flute, breathy Zen meditation and dramatic tone bends"
  },
  {
    id: "Shamisen",
    name: "Shamisen",
    icon: "mdi:guitar-acoustic",
    color: "%238B0000",
    style: "",
    styles: ["all", "japanese_trad"],
    promptDesc: "three-string plucked shamisen, striking bachi plectrum with percussive attack"
  },
  {
    id: "Taiko",
    name: "Taiko",
    icon: "game-icons:drum",
    color: "%23B22222",
    style: "transform: scale(1.2);",
    styles: ["all", "japanese_trad", "cinematic"],
    promptDesc: "Japanese large taiko drums, thunderous dynamic ensemble percussion"
  },

  // ==========================================
  // TRADICIONAL AFRICÀ I LLATINOAMERICÀ
  // ==========================================
  {
    id: "Kora",
    name: "Kora",
    icon: "game-icons:harp",
    color: "%23FF8C00",
    style: "",
    styles: ["all", "african_trad", "contemporary_folk"],
    promptDesc: "West African 21-string harp-lute kora, shimmering intricate polyrhythmic arpeggios"
  },
  {
    id: "Mbira",
    name: "Mbira (Kalimba)",
    icon: "game-icons:piano-keys",
    color: "%23CD853F",
    style: "",
    styles: ["all", "african_trad", "ambient"],
    promptDesc: "African thumb piano mbira kalimba, metallic plucking with bottle-cap buzz and warm resonance"
  },
  {
    id: "Balafon",
    name: "Balafó",
    icon: "game-icons:xylophone",
    color: "%238B4513",
    style: "",
    styles: ["all", "african_trad"],
    promptDesc: "wooden key balafon marimba with gourd resonators, buzzy bright melodic percussion"
  },
  {
    id: "Djembe",
    name: "Djembé",
    icon: "game-icons:drum",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "african_trad"],
    promptDesc: "West African djembe drum, resonant bass, tone and crisp slap strokes"
  },
  {
    id: "Charango",
    name: "Charango",
    icon: "mdi:guitar-acoustic",
    color: "%23D2691E",
    style: "",
    styles: ["all", "latin_american", "contemporary_folk"],
    promptDesc: "Andean charango small lute, rapid high-pitched double-strum rasgueos"
  },
  {
    id: "Quena",
    name: "Quena",
    icon: "game-icons:flute",
    color: "%23DEB887",
    style: "",
    styles: ["all", "latin_american"],
    promptDesc: "traditional Andean notched quena flute, breathy woody emotional melodies"
  },
  {
    id: "Zampona",
    name: "Zampoña",
    icon: "game-icons:pan-flute",
    color: "%23CD853F",
    style: "",
    styles: ["all", "latin_american"],
    promptDesc: "Andean panpipe zampoña siku, airy double-row cane pipes played in hocket"
  },
  {
    id: "Cajon",
    name: "Cajón",
    icon: "game-icons:drum",
    color: "%235C4033",
    style: "",
    styles: ["all", "latin_american", "iberian_folk", "catalan_trad", "contemporary_folk"],
    promptDesc: "Peruvian and flamenco wooden cajón box drum, punchy low bass and snappy snare slap"
  },

  // ==========================================
  // ORQUESTRAL I INSTRUMENTS MODERNS
  // ==========================================
  {
    id: "Viola",
    name: "Viola",
    icon: "mdi:violin",
    color: "%238B4513",
    style: "transform: scale(1.08);",
    styles: ["all", "classical", "romanticism", "orchestral", "cinematic"],
    promptDesc: "orchestral viola, warm dark mellow bowed string voice"
  },
  {
    id: "Piccolo",
    name: "Flautí (Piccolo)",
    icon: "game-icons:flute",
    color: "%234682B4",
    style: "transform: scale(0.8);",
    styles: ["all", "classical", "romanticism", "orchestral"],
    promptDesc: "orchestral piccolo, brilliant sparkling high register woodwind"
  },
  {
    id: "English Horn",
    name: "Corno anglès",
    icon: "game-icons:clarinet",
    color: "%233E2723",
    style: "",
    styles: ["all", "romanticism", "orchestral", "cinematic"],
    promptDesc: "cor anglais French tenor oboe, melancholy lyrical double reed"
  },
  {
    id: "Bass Clarinet",
    name: "Clarinet baix",
    icon: "game-icons:clarinet",
    color: "%231C1C1C",
    style: "transform: scale(1.2);",
    styles: ["all", "romanticism", "orchestral", "cinematic", "jazz"],
    promptDesc: "bass clarinet, velvety woody deep low register woodwind"
  },
  {
    id: "French Horn",
    name: "Trompa (Corn)",
    icon: "game-icons:hunting-horn",
    color: "%23DAA520",
    style: "",
    styles: ["all", "classical", "romanticism", "orchestral", "cinematic"],
    promptDesc: "French horn, noble mellow brass calls and soaring orchestral anthems"
  },
  {
    id: "Modern Tuba",
    name: "Tuba orquestral",
    icon: "game-icons:trombone",
    color: "%23B8860B",
    style: "transform: scale(1.25);",
    styles: ["all", "romanticism", "orchestral", "cinematic"],
    promptDesc: "orchestral brass tuba, deep foundational low brass weight"
  },
  {
    id: "Timpani",
    name: "Timbales orquestrals",
    icon: "game-icons:drum",
    color: "%238B5A2B",
    style: "",
    styles: ["all", "classical", "romanticism", "orchestral", "cinematic"],
    promptDesc: "orchestral kettle drums timpani, tuned dynamic dramatic thunder"
  },
  {
    id: "Glockenspiel",
    name: "Glockenspiel",
    icon: "game-icons:xylophone",
    color: "%23ADD8E6",
    style: "",
    styles: ["all", "classical", "romanticism", "orchestral", "pop"],
    promptDesc: "orchestral glockenspiel, bright crystalline steel bell mallet strikes"
  },
  {
    id: "Xylophone",
    name: "Xilòfon",
    icon: "game-icons:xylophone",
    color: "%23CD853F",
    style: "",
    styles: ["all", "classical", "orchestral", "contemporary_folk"],
    promptDesc: "acoustic xylophone, dry snappy wooden pitched mallet resonance"
  },
  {
    id: "Marimba",
    name: "Marimba",
    icon: "game-icons:xylophone",
    color: "%238B4513",
    style: "",
    styles: ["all", "orchestral", "contemporary_folk", "latin_american", "ambient"],
    promptDesc: "rosewood concert marimba, warm deep velvety wooden tone"
  },
  {
    id: "Vibraphone",
    name: "Vibràfon",
    icon: "game-icons:xylophone",
    color: "%234682B4",
    style: "",
    styles: ["all", "jazz", "orchestral", "ambient"],
    promptDesc: "jazz vibraphone with motorized tremolo fans, shimmering warm metallic sustain"
  },
  {
    id: "Celesta",
    name: "Celesta",
    icon: "game-icons:piano-keys",
    color: "%23E6E6FA",
    style: "",
    styles: ["all", "romanticism", "orchestral", "cinematic"],
    promptDesc: "orchestral celesta keyboard, bell-like magical fairy-tale timbre"
  },
  {
    id: "Gong",
    name: "Gong (Tam-tam)",
    icon: "lucide:drum",
    color: "%23FFD700",
    style: "",
    styles: ["all", "orchestral", "cinematic", "ambient"],
    promptDesc: "large orchestral tam-tam gong, colossal crashing wash and deep shimmering decay"
  },
  {
    id: "Hammond Organ",
    name: "Òrgan Hammond",
    icon: "game-icons:pipe-organ",
    color: "%238B0000",
    style: "",
    styles: ["all", "blues", "rock", "jazz"],
    promptDesc: "Hammond B3 tonewheel organ with Leslie rotating speaker swirl and drawbar growl"
  },
  {
    id: "Mellotron",
    name: "Mellotron",
    icon: "game-icons:piano-keys",
    color: "%234A2E12",
    style: "",
    styles: ["all", "rock", "pop", "ambient"],
    promptDesc: "vintage tape-replay Mellotron, nostalgic lo-fi flute and string tapes"
  }
];

// Helper per export / consum en frontend i Node.js
if (typeof window !== 'undefined') {
  window.STYLES = STYLES;
  window.CATALOG_INSTRUMENTS = CATALOG_INSTRUMENTS;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { STYLES, CATALOG_INSTRUMENTS };
}
