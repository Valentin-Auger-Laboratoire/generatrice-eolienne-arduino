// Génératrice d'éolienne : version 2026 (réécrite à partir du programme et du montage de 2024)
//
// Ce qui change par rapport à 2024 (voir docs/brochage.md et le README) :
//  - la génératrice n'arrive plus directement sur A0 : redresseur, condensateur, pont diviseur
//    33 kΩ / 10 kΩ et diode Zener 5,1 V protègent l'entrée (jusqu'à environ 20 V mesurables) ;
//  - la tension est convertie en volts et lissée (moyenne glissante sur 8 mesures) ;
//  - hystérésis : relais fermé au-dessus de 3,0 V, ouvert sous 2,5 V (plus de claquements
//    quand le vent hésite autour du seuil) ;
//  - temps minimal de 2 s entre deux changements d'état du relais ;
//  - boucle non bloquante (millis), mesure toutes les 50 ms, une ligne CSV toutes les 500 ms ;
//  - la LED intégrée (D13) recopie l'état du relais.
// Le contact COM du relais doit être relié au +5 V pour que la LED (sur NO) s'allume.

const uint8_t PIN_GENERATRICE = A0;
const uint8_t PIN_RELAIS = 8;
const uint8_t PIN_LED_CARTE = LED_BUILTIN;

const float VREF = 5.0;                 // tension de référence du CAN (V)
const float R_HAUT = 33000.0;           // pont diviseur : génératrice → R_HAUT → A0 → R_BAS → GND
const float R_BAS = 10000.0;
const float RAPPORT = (R_HAUT + R_BAS) / R_BAS;   // 4,3

const float SEUIL_ON = 3.0;             // V côté génératrice (après redressement)
const float SEUIL_OFF = 2.5;            // V
const unsigned long PERIODE_MESURE = 50;        // ms
const unsigned long PERIODE_AFFICHAGE = 500;    // ms
const unsigned long DUREE_MIN_ETAT = 2000;      // ms entre deux commutations

const uint8_t N_MOYENNE = 8;
float mesures[N_MOYENNE];
uint8_t indice = 0;
bool tableauPlein = false;

bool relaisFerme = false;
unsigned long dernierChangement = 0;
unsigned long derniereMesure = 0;
unsigned long dernierAffichage = 0;

float lireTensionGeneratrice() {
  int brut = analogRead(PIN_GENERATRICE);
  return brut * VREF / 1023.0 * RAPPORT;
}

float moyenne() {
  uint8_t n = tableauPlein ? N_MOYENNE : indice;
  if (n == 0) return 0.0;
  float s = 0;
  for (uint8_t i = 0; i < n; i++) s += mesures[i];
  return s / n;
}

void commanderRelais(bool fermer, unsigned long maintenant) {
  if (fermer == relaisFerme) return;
  if (maintenant - dernierChangement < DUREE_MIN_ETAT) return;   // anti-claquement
  relaisFerme = fermer;
  dernierChangement = maintenant;
  digitalWrite(PIN_RELAIS, relaisFerme ? HIGH : LOW);
  digitalWrite(PIN_LED_CARTE, relaisFerme ? HIGH : LOW);
}

void setup() {
  pinMode(PIN_RELAIS, OUTPUT);
  pinMode(PIN_LED_CARTE, OUTPUT);
  digitalWrite(PIN_RELAIS, LOW);
  digitalWrite(PIN_LED_CARTE, LOW);
  Serial.begin(9600);
  Serial.println(F("t_ms,tension_V,moyenne_V,relais"));
}

void loop() {
  unsigned long maintenant = millis();

  if (maintenant - derniereMesure >= PERIODE_MESURE) {
    derniereMesure = maintenant;
    mesures[indice] = lireTensionGeneratrice();
    indice = (indice + 1) % N_MOYENNE;
    if (indice == 0) tableauPlein = true;

    float v = moyenne();
    if (!relaisFerme && v > SEUIL_ON) commanderRelais(true, maintenant);
    else if (relaisFerme && v < SEUIL_OFF) commanderRelais(false, maintenant);
  }

  if (maintenant - dernierAffichage >= PERIODE_AFFICHAGE) {
    dernierAffichage = maintenant;
    uint8_t dernier = (indice + N_MOYENNE - 1) % N_MOYENNE;
    Serial.print(maintenant);            Serial.print(',');
    Serial.print(mesures[dernier], 2);   Serial.print(',');
    Serial.print(moyenne(), 2);          Serial.print(',');
    Serial.println(relaisFerme ? 1 : 0);
  }
}
