// analog multiplexer MC14051B
// https://www.raspberry-pi-geek.com/Archive/2016/15/Write-your-own-drivers-for-Arduino

#ifndef MC14051B_h
#define MC14051B_h

#include <Arduino.h>

class MC14051B
{
  public:
      MC14051B(int controlPin, int APin, int BPin, int CPin, int X);
      ~MC14051B();
      int mcAnalogRead(char pin);
      void mcAnalogWrite(char pin, int value);
      void reset();

 private:
      int _ABC[3];
      int pinX;
      int controlPin;
      void setABCPin(char pin);
};

#endif
