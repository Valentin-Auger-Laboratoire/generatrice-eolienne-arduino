// Génératrice d'éolienne : programme de juillet 2024
// Recopié à l'identique depuis mon document « Projet Eolienne - Code Arduino et Explications ».
// Câblage prévu : sortie + de la génératrice sur A0 (sortie − sur GND), commande du relais sur D8,
// LED en série avec une résistance de 220 Ω entre la sortie NO du relais et GND.

const int pinGenerateur = A0;  // Entrée analogique pour le générateur
const int pinRelais = 8;       // Sortie numérique pour contrôler le relais
const int seuilTension = 100;  // Seuil de tension (0-1023, ajuster selon besoin)

// Fonction d'initialisation
void setup() {
  pinMode(pinGenerateur, INPUT);  // Broche du générateur en entrée
  pinMode(pinRelais, OUTPUT);     // Broche du relais en sortie
  digitalWrite(pinRelais, LOW);   // Assurez-vous que le relais est éteint au départ
  Serial.begin(9600);             // Initialisation de la communication série pour le débogage
}

// Boucle principale
void loop() {
  int tension = analogRead(pinGenerateur);  // Lecture de la tension du générateur
  Serial.print("Tension lue: ");
  Serial.println(tension);
  if (tension > seuilTension) {     // Vérification si la tension dépasse le seuil
    digitalWrite(pinRelais, HIGH);  // Si la tension est suffisante, activer le relais
  } else {
    digitalWrite(pinRelais, LOW);   // Sinon, éteindre le relais
  }
  delay(100);  // Petite pause avant la prochaine lecture
}
