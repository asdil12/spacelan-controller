/* Benjamin Aigner, 2022 <beni@asterics-foundation.org> */
/* Public domain / CC 0 */

/** example code using all possibilities of the Joystick class
 * for the RP2040.
 */

#include <Joystick.h>
#include "MC14051B.h"

int poti = 0;
int poti1 = 0;
float btn1 = 0;

int potis[50] = {0};
int potis_max[50];
int potis_min[50];
float buttons[50] = {0};
//MC14051B expander(4, 5, 6, 7, A2);

int get_poti(int gpio_pin) {
  int newpoti = analogRead(gpio_pin);
  // debounce
  potis[gpio_pin] = (potis[gpio_pin] * 49 + newpoti) / 50;
  int p = potis[gpio_pin];
  Serial.print(p);
  Serial.print("\t");
  // auto calibrate
  potis_max[gpio_pin] = max(p, potis_max[gpio_pin]);
  if (p)
    potis_min[gpio_pin] = min(p, potis_min[gpio_pin]);

  // snap to min, max and middle

  if (p < 10) p = 0;
  if (p > 1013) p = 1023;
  int deadzone = 70;
  if (p > 512-deadzone && p < 512+deadzone) p = 512; // delta to 512
  Serial.print(p);
  Serial.print("\t");

  Serial.print(potis_min[gpio_pin]);
  Serial.print("\t");
  Serial.print(potis_max[gpio_pin]);
  Serial.print("\t");
  int delta_min = 512 - potis_min[gpio_pin];
  int delta_max = potis_max[gpio_pin] - 512;
  int delta = min(delta_min, delta_max);
  int min_min = 512 - delta;
  int max_max = 512 + delta;
  //int min_min = max(potis_min[gpio_pin], 512 - (potis_max[gpio_pin] - 512));
  //int max_max = min(potis_max[gpio_pin], 512 + (512 - potis_min[gpio_pin]));
  Serial.print(min_min);
  Serial.print("\t");
  Serial.print(max_max);
  Serial.print("\t");
  //int p = 1024 * (p - min_min) / (float)(max_max - min_min);
  if (max_max - min_min != 0)
    p = (p - min_min) * (1023) / (max_max - min_min);
  p = min(p, 1023);
  p = max(p, 0);


  return p;
}

bool get_button(int gpio_pin) {
  int newbutton = !digitalRead(gpio_pin);
  // debounce
  buttons[gpio_pin] = (buttons[gpio_pin] * 29 + newbutton) / 30;
  return buttons[gpio_pin] > 0.5;
}

void setup() {
  Serial.begin(115200);
  Serial.println("Use BOOTSEL to start the Joystick demo.");
  Joystick.begin();
  pinMode(22, INPUT_PULLUP);
  for (int i=0; i<50; i++) {
    potis_min[i] = 307; // 1023*0.3
    potis_max[i] = 614; // 1023*0.6
  }
}

void loop() {
  int p1 = get_poti(A0);
  int p2 = get_poti(A1);

  bool b1 = get_button(22);

  Joystick.X(p1);
  Joystick.Y(p2);

  Joystick.button(1, b1);

  Serial.print(p1);
  Serial.print("\t");

  Serial.print(p2);
  Serial.print("\t");

  Serial.println(b1);

  /*
  if (BOOTSEL) {
	Serial.println("Joystick buttons");
    for(uint8_t i = 1; i<=32; i++)
    {
		Joystick.button(i,true);
		delay(250);
		Joystick.button(i,false);
		delay(10); //we need a short delay here, sending packets with less than 1ms leads to packet loss!
	}
	//alternativ with manual send:
	Joystick.useManualSend(true);
	Serial.println("Joystick buttons - manual send");
    for(uint8_t i = 1; i<=32; i++)
    {
		Joystick.button(i,true);
		Joystick.send_now();
		delay(250);
		Joystick.button(i,false);
	}
	Joystick.useManualSend(false);
	
    //iterate all joystick axis
    //Note: although you can use 0-1023 here (10bit), internally 8bits are used (-127 to 127)
    Serial.println("Joystick X");
    for(uint16_t i = 0; i<1023; i++) { Joystick.X(i); delay(2); } Joystick.X(512);
    Serial.println("Joystick Y");
    for(uint16_t i = 0; i<1023; i++) { Joystick.Y(i); delay(2); } Joystick.Y(512);
    Serial.println("Joystick Z");
    for(uint16_t i = 0; i<1023; i++) { Joystick.Z(i); delay(2); } Joystick.Z(512);
    Serial.println("Joystick Zrotate");
    for(uint16_t i = 0; i<1023; i++) { Joystick.Zrotate(i); delay(2); } Joystick.Zrotate(512);
    Serial.println("Joystick sliderLeft");
    for(uint16_t i = 0; i<1023; i++) { Joystick.sliderLeft(i); delay(2); } Joystick.sliderLeft(0);
    Serial.println("Joystick sliderRight");
    for(uint16_t i = 0; i<1023; i++) { Joystick.sliderRight(i); delay(2); } Joystick.sliderRight(0);
    Serial.println("Joystick hat");
    for(uint16_t i = 0; i<360; i++) { Joystick.hat(i); delay(20); } Joystick.hat(-1);
    
    //use int8 mode for the axis.
    //Note: hat is not used differently.
    Serial.println("Now all axis in 8bit mode, -127 to 127");
    Joystick.use8bit(true);
    Serial.println("Joystick X");
    for(int16_t i = -127; i<128; i++) { Joystick.X(i); delay(2); } Joystick.X(0);
    Serial.println("Joystick Y");
    for(int16_t i = -127; i<128; i++) { Joystick.Y(i); delay(2); } Joystick.Y(0);
    Serial.println("Joystick Z");
    for(int16_t i = -127; i<128; i++) { Joystick.Z(i); delay(2); } Joystick.Z(0);
    Serial.println("Joystick Zrotate");
    for(int16_t i = -127; i<128; i++) { Joystick.Zrotate(i); delay(2); } Joystick.Zrotate(0);
    Serial.println("Joystick sliderLeft");
    for(int16_t i = -127; i<128; i++) { Joystick.sliderLeft(i); delay(2); } Joystick.sliderLeft(0);
    Serial.println("Joystick sliderRight");
    for(int16_t i = -127; i<128; i++) { Joystick.sliderRight(i); delay(2); } Joystick.sliderRight(0);
    Joystick.use8bit(false);
  }
  */
}
