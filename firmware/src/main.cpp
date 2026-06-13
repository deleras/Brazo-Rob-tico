#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define NUM_SERVOS 7 

// Pin digital asignado al relé de la bomba de vacío / ventosa
#define PIN_BOMBA 4  

// Canales mapeados en tu PCA9685
int servoPins[NUM_SERVOS] = {0, 2, 4, 7, 8, 12, 15}; 

void setup() {
  // Velocidad de comunicación síncrona acoplada con la HMI
  Serial.begin(115200); 
  
  // Configuración del pin de la bomba
  pinMode(PIN_BOMBA, OUTPUT);
  digitalWrite(PIN_BOMBA, LOW); // Apagada por defecto

  // Inicialización del módulo PCA9685
  pwm.begin();
  pwm.setPWMFreq(50); 

  // Postura inicial de seguridad anti-sobrecarga (350 = Centro controlado)
  for (int i = 0; i < NUM_SERVOS; i++) {
    pwm.setPWM(servoPins[i], 0, 350);
    delay(50); // Pequeño retraso para mitigar picos de corriente súbitos
  }
}

void loop() {
  // Esperamos a que haya datos en el búfer serial antes de procesar
  if (Serial.available() > 0) {
    
    // Serial.parseInt() extrae secuencialmente cada número ignorando las comas
    int m1 = Serial.parseInt();
    int m2 = Serial.parseInt();
    int m3 = Serial.parseInt();
    int m4 = Serial.parseInt();
    int m5 = Serial.parseInt();
    int m6 = Serial.parseInt();
    int m7 = Serial.parseInt();
    int estadoBomba = Serial.parseInt(); // Ahora lee un entero: 1 (ON) o 0 (OFF)

    // Al encontrar el salto de línea '\n', descartamos cualquier residuo flotante
    if (Serial.read() == '\n' || true) {
      
      // Validación industrial: Ignoramos lecturas de ruido (0) fuera de rango del PCA9685
      if (m1 > 0 && m2 > 0 && m3 > 0 && m7 > 0) {
        
        // Inyección de pulsos directa al controlador de servos
        pwm.setPWM(servoPins[0], 0, m1);
        pwm.setPWM(servoPins[1], 0, m2);
        pwm.setPWM(servoPins[2], 0, m3);
        pwm.setPWM(servoPins[3], 0, m4);
        pwm.setPWM(servoPins[4], 0, m5);
        pwm.setPWM(servoPins[5], 0, m6);
        pwm.setPWM(servoPins[6], 0, m7);

        // Control digital binario del actuador final (Ventosa)
        if (estadoBomba == 1) {
          digitalWrite(PIN_BOMBA, HIGH); // Activa relé
        } else {
          digitalWrite(PIN_BOMBA, LOW);  // Desactiva relé
        }
      }
    }
  }
}