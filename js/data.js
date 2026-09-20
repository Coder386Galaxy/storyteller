// ============ STORY DATA LIBRARY ============

const NAMES = {
  first: {
    fantasy: ["Elara","Kael","Seraphina","Theron","Liora","Rook","Wren","Briar","Caspian","Isolde","Thorne","Morrigan","Darian","Lyra","Ronan","Aveline","Rowan","Finn"],
    scifi: ["Aria","Kai","Nova","Cyrus","Zara","Jax","Luna","Orion","Vega","Dax","Nyx","Talon","Sable","Rin","Kael","Vex"],
    mystery: ["Margot","Ellis","Vivian","Clark","Irene","Dashiell","Ruth","Flynn","Cora","Holden","June","Raylan","Agnes","Nora"],
    horror: ["Eleanor","Silas","Rowan","Amity","Jonas","Cordelia","Ichabod","Minerva","Thaddeus","Pandora","Judas","Delilah","Caleb","Marnie"],
    western: ["Jesse","Cole","Abigail","Silas","Mae","Wyatt","Clara","Rufus","Dolly","Hank","Ruby","Eli","Bonnie","Clyde"],
    pirate: ["Rafe","Morgana","Calico","Silvers","Isla","Barnaby","Cressida","Thatch","Marina","Drake","Bramble","Jezebel"],
    detective: ["Veronica","Marlowe","Pippa","Reid","Simone","Dexter","Helena","Bruno","Zora","Conway"],
    general: ["Ada","Beatrice","Benjamin","Clara","Daniel","Elena","Felix","Greta","Hugo","Ivy","Julian","Mira","Nico","Olive","Paul","Amelia","Finn","Scout","Ethan","Poppy","Will","Lucy","Miles","Evie","Jasper","Rosie","Henry","Sage"]
  },
  last: {
    fantasy: ["Ashbourne","Blackthorn","Stormwind","Silverleaf","Ironvein","Moonwhisper","Ravencroft","Goldweaver","Winterbourne","Thornfield"],
    scifi: ["Voss","Rainer","Kade","Quinn","Hex","Wyre","Pike","Slate","Arkwright","Tesslar","Vance"],
    mystery: ["Blackwood","Sterling","Monroe","Holloway","Greene","Colton","Ashby","Frost","Mercer","Tinsley"],
    horror: ["Graves","Mortlock","Ashcroft","Crowe","Grimm","Hollow","Bleak","Thornhill","Nightshade","Hemlock"],
    western: ["Hawkins","McCall","Boone","Colter","Hickok","Russell","Yates","Pratt","Garrett","Monroe"],
    pirate: ["Blackwater","Keelhaul","Redgrace","Salt","Cutler","O'Malley","Vane","Hawkins","Bellamy","Bonnet"],
    detective: ["Parker","Spade","Magnusson","Archer","Cross","Quinn","Doyle","Marsh","Blackwell","Monk"],
    general: ["Brooks","Hayes","Bennett","Carter","Morrison","Reed","Stone","Wade","Wells","Clarke","Ford","Gray","Hawthorne","Darcy","Blake","Reyes","Cartwright"]
  },
  titles: ["the Bold","the Cunning","the Lost","the Unbroken","the Pale","the Forgotten","the Ash","the Quiet","the Red","the Silver","the Wanderer","the Broken","the Fierce","the Gentle","of the Hollow","of the Wild","of the North","of the Mists"]
};

const CREATURES = {
  fantasy: ["dragon","griffin","wraith","goblin horde","ancient treant","talking fox","chimera","basilisk","cursed knight","fae queen","shadow wolf","giant eagle"],
  scifi: ["rogue AI","silicon-based lifeform","genetically engineered beast","nanite swarm","void entity","cybernetic bounty hunter","quantum anomaly","alien hivemind"],
  mystery: ["shadowy figure","masked stranger","blackmailer","copycat killer","unknown stalker","mysterious caller","unexpected witness"],
  horror: ["demon","vengeful spirit","skin-walker","cursed doll","the thing in the walls","faceless watcher","the hollow children","the Smiling Man"],
  western: ["notorious outlaw","renegade Comanche war party","corrupt sheriff","vengeful gunslinger","band of desperadoes"],
  pirate: ["sea monster","ghost ship","kraken","cursed crew","rival captain","the deep ones","mermaid queen","undead pirate lord"],
  general: ["stranger","wild beast","band of thieves","mysterious traveler","shadow that follows","old enemy","vengeful ghost","fugitive prince"]
};

const LOCATIONS = {
  fantasy: ["crumbling castle","ancient forest of silver pines","walled city of stone and steam","monastery carved into a mountain","subterranean dwarf-hold","floating archipelago","swamp of whispering reeds","desert of glass and bone"],
  scifi: ["derelict space station","mining colony on a frozen moon","neon-drenched megacity sprawl","generation ship adrift between stars","biodome failing on a hostile world","black-market asteroid","military orbital platform"],
  mystery: ["seaside boarding house","remote mountain lodge","prep school library","locked study","foggy dockside warehouse","small-town diner at 2am","Victorian theatre","snowed-in manor"],
  horror: ["abandoned asylum","house where time doesn't work right","church with no cross","cabin in the silent woods","hotel that wasn't there yesterday","suburban basement","empty orphanage","lighthouse in perpetual storm"],
  western: ["dusty saloon","abandoned mine","ranch under siege","railroad camp","border cantina","deserted mission","ghost town","fort on the frontier"],
  pirate: ["skull-shaped cove","smuggler's den","floating tavern made of wrecked ships","cavern of coral and bones","captain's cursed quarters","treasure island with no beach","port where the tide never comes"],
  general: ["crossroads at midnight","small village square","ancient bridge","overgrown garden","locked attic","throne room","tavern hearth","mountain pass in winter"]
};

const ITEMS = {
  fantasy: ["silver dagger","worn map","enchanted amulet","healing potion","rusted key","bag of gold coins","dragon-scale","old letter sealed with wax","rune-carved staff","holy symbol"],
  scifi: ["plasma pistol","data chip","med-kit","hacking device","oxygen canister","ration pack","EMP grenade","quantum key","neural link","antidote vial"],
  mystery: ["crumpled note","old photograph","blood-stained glove","brass key","pocket watch","revolver","train ticket","fingerprint kit","encrypted diary","lipstick-stained handkerchief"],
  horror: ["torn page from a Bible","cursed locket","flickering candle","silver bullet","chalk for circles","holy water","child's doll","tarnished mirror","creaky floorboard (as a weapon?)"],
  western: ["six-shooter","shotgun","dynamite stick","canteen","whiskey flask","lasso","wanted poster","silver dollar","horseshoe nail","telegraph key"],
  pirate: ["cutlass","spyglass","rum flask","treasure map fragment","pistol","rope","compass that doesn't point north","pearl necklace","cursed doubloon","tinderbox"],
  general: ["knife","length of rope","torch","loaf of bread","pouch of coins","cloak","lantern","journal","flask of water","mysterious key"]
};

const COMPLICATIONS = [
  "The ground shifts beneath you.",
  "A sound in the distance makes you freeze.",
  "You realize you are not alone.",
  "Something you trusted turns out to be a lie.",
  "An old wound throbs painfully.",
  "A figure you thought long gone appears in the corner of your eye.",
  "The weather turns violently.",
  "Time seems to slow for a heartbeat.",
  "You hear your own name spoken by a voice you don't recognize.",
  "The lights go out.",
  "A door you thought was locked swings open on its own.",
  "Your stomach drops — something is very wrong."
];

const MOODS = ["foreboding","hopeful","tense","melancholic","thrilling","suspicious","enchanted","claustrophobic","serene","oppressive","eerie","celebratory","mournful","electric"];

const OPENINGS = {
  fantasy: ["You wake in a dungeon cell, your armor gone and a strange sigil carved into the stone above you.","The king's messenger collapses at your door with an arrow in his back and a sealed message for you.","A talking raven lands on your windowsill and addresses you by a name you haven't used in years."],
  scifi: ["Your ship's alarms blare — you've dropped out of FTL at the wrong coordinates and there's something massive on the sensors.","The cryo-pod across from yours opens a full century early, and the person inside isn't on the crew manifest.","A distress signal in a dead language repeats on every frequency, and your AI refuses to translate it."],
  mystery: ["You arrive at the isolated inn to find that the other guests all seem to know your name.","The body in the library isn't who the police think it is, and you alone saw the real killer escape.","A letter arrives postmarked the day after tomorrow, warning you not to answer the door at midnight."],
  horror: ["Something has been knocking your wall in threes for three nights. Tonight, the knocking starts before sundown.","Your reflection in the mirror smiles when you don't.","The child you pulled from the woods hasn't spoken in three days — but keeps drawing pictures of the inside of your house."],
  western: ["Your horse dies of snakebite twenty miles from the nearest water, and you can see dust on the horizon from approaching riders.","The sheriff pins a wanted poster to the board — and the face on it is yours, accused of a murder you didn't commit.","A stranger in black sits down across from you at the saloon and slides a box across the table. 'Don't open it until sundown.'"],
  pirate: ["You wake in the brig of your own ship; there's been a mutiny and they're voting in a new captain at dawn.","The treasure map you've been chasing leads to an island not on any chart — and the water around it is unnaturally still.","A bottle washes up on deck containing a letter in your own handwriting, one you haven't written yet."],
  general: ["You wake in an unfamiliar room with no memory of how you got there and a strange object in your pocket.","The letter arrives at breakfast, delivered by a hand you don't see. It contains only three words: 'They know.'","The road ahead splits in two, and you can hear singing coming from both directions."]
};

const CONJUNCTIONS = ["But then","Meanwhile","Just then","Unexpectedly","Simultaneously","At that moment","Before you can react","Without warning","Almost immediately"];

// Positive, neutral, negative outcomes keyed by situation types
const FLAVOR = {
  win: ["You succeed brilliantly!","Victory is yours!","It works better than you dared hope.","Fortune smiles on you.","Your skill prevails."],
  partial: ["You succeed, but not without cost.","It works — sort of.","You get what you want, but something feels off.","A partial victory, better than nothing."],
  lose: ["It goes badly.","Fortune deserts you.","The attempt fails, and the situation worsens.","Not every risk pays off."],
  damage: ["You take a wound.","Pain lances through you.","Something inside you cracks.","You're hurt, but standing."],
  gain: ["You pick up something useful.","An item catches your eye.","You find something unexpected."]
};
