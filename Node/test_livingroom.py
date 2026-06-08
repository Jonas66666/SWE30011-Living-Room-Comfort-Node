/*
 * Living Room Node - Compatible with Unified Dashboard
 * Sends: temp=xx,light=xx,motion=x,fan=x,led=x
 * Receives: fan_on, fan_off, light_on, light_off
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// ==================== PIN DEFINITIONS ====================
#define DHTPIN 10
#define DHTTYPE DHT11
#define PIRPIN 3
#define RELAY_FAN 4      // Fan relay (LOW = ON)
#define LED_PIN 6        // Direct LED control (HIGH = ON)
#define LDRPIN A0

// ==================== LCD SETUP ====================
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ==================== DHT OBJECT ====================
DHT dht(DHTPIN, DHTTYPE);

// ==================== VARIABLES ====================
float temperature = 0;
float humidity = 0;
int motion = 0;
int light = 0;
bool fanState = false;
bool ledState = false;

// Motion timing
unsigned long lastMotionTime = 0;
bool occupied = false;

// Settings
const float TEMP_THRESHOLD = 26.0;
const int LIGHT_THRESHOLD = 100;
const unsigned long TIMEOUT_MS = 300000;  // 5 minutes

// String for incoming commands
String inputString = "";

// ==================== SETUP ====================
void setup() {
  Serial.begin(9600);
  
  pinMode(PIRPIN, INPUT);
  pinMode(RELAY_FAN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(LDRPIN, INPUT);
  
  digitalWrite(RELAY_FAN, HIGH);   // Relay OFF
  digitalWrite(LED_PIN, LOW);      // LED OFF
  
  dht.begin();
  
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Living Room Node");
  lcd.setCursor(0, 1);
  lcd.print("Ready...");
  
  delay(2000);
  lcd.clear();
  
  Serial.println("Living Room Node Ready");
}

// ==================== MAIN LOOP ====================
void loop() {
  readSensors();
  checkMotion();
  checkSerialCommands();
  controlDevices();
  updateLCD();
  sendStatus();
  
  delay(200);
}

// ==================== READ SENSORS ====================
void readSensors() {
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  light = analogRead(LDRPIN);
  
  if (isnan(humidity) || isnan(temperature)) {
    humidity = 0;
    temperature = 0;
  }
}

// ==================== CHECK MOTION ====================
void checkMotion() {
  int currentMotion = digitalRead(PIRPIN);
  
  if (currentMotion == HIGH) {
    lastMotionTime = millis();
    if (!occupied) {
      occupied = true;
    }
  }
  
  if (occupied && (millis() - lastMotionTime) >= TIMEOUT_MS) {
    occupied = false;
  }
  
  motion = currentMotion;
}

// ==================== CHECK SERIAL COMMANDS ====================
void checkSerialCommands() {
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      processCommand(inputString);
      inputString = "";
    } else if (inChar != '\r') {
      inputString += inChar;
    }
  }
}

void processCommand(String command) {
  command.trim();
  command.toLowerCase();
  
  Serial.print("Command received: ");
  Serial.println(command);
  
  if (command == "fan_on") {
    fanState = true;
    digitalWrite(RELAY_FAN, LOW);
    Serial.println("Fan turned ON");
  }
  else if (command == "fan_off") {
    fanState = false;
    digitalWrite(RELAY_FAN, HIGH);
    Serial.println("Fan turned OFF");
  }
  else if (command == "light_on") {
    ledState = true;
    digitalWrite(LED_PIN, HIGH);
    Serial.println("LED turned ON");
  }
  else if (command == "light_off") {
    ledState = false;
    digitalWrite(LED_PIN, LOW);
    Serial.println("LED turned OFF");
  }
}

// ==================== CONTROL DEVICES ====================
void controlDevices() {
  // Only auto-control if not manually overridden by cloud?
  // For now, let cloud commands take priority
  // Auto-control only when no manual command recently
  
  // You can add auto logic here, but cloud commands override
}

// ==================== LCD DISPLAY ====================
void updateLCD() {
  static unsigned long lastUpdate = 0;
  
  if (millis() - lastUpdate >= 1000) {
    lastUpdate = millis();
    
    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print(temperature, 1);
    lcd.print("C ");
    
    lcd.setCursor(8, 0);
    lcd.print("L:");
    lcd.print(light / 10);
    
    lcd.setCursor(0, 1);
    if (occupied) {
      lcd.print("OCCUPIED ");
    } else {
      lcd.print("EMPTY    ");
    }
    
    lcd.setCursor(10, 1);
    if (fanState) lcd.print("F");
    if (ledState) lcd.print("L");
  }
}

// ==================== SEND STATUS (key=value format) ====================
void sendStatus() {
  static unsigned long lastSend = 0;
  
  if (millis() - lastSend >= 2000) {
    lastSend = millis();
    
    // Format: temp=xx,light=xx,motion=x,fan=x,led=x
    Serial.print("temp=");
    Serial.print(temperature, 1);
    Serial.print(",light=");
    Serial.print(light);
    Serial.print(",motion=");
    Serial.print(occupied ? 1 : 0);
    Serial.print(",fan=");
    Serial.print(fanState ? "on" : "off");
    Serial.print(",led=");
    Serial.println(ledState ? "on" : "off");
  }
}