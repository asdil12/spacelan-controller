#include <Arduino.h>
#include "MC14051B.h"

MC14051B::MC14051B(int controlPin, int APin, int BPin, int CPin, int X)
{
    pinMode(controlPin, OUTPUT);
    pinMode(APin, OUTPUT);
    pinMode(BPin, OUTPUT);
    pinMode(CPin, OUTPUT);
    _ABC[0] = APin;
    _ABC[1] = BPin;
    _ABC[2] = CPin;
    controlPin=controlPin;
    pinX=X;
}

int MC14051B::mcAnalogRead(char pin)
{
    pinMode(pinX, INPUT);

    setABCPin(pin);
    return(analogRead(pinX));
}

void MC14051B::mcAnalogWrite(char pin, int value)
{
    pinMode(pinX, OUTPUT);

    setABCPin(pin);
    analogWrite(pinX, value);
}

void MC14051B::setABCPin(char pin)
{
    int i;

    for (i=0; i<3; i++)
    {
        digitalWrite(_ABC[i], bitRead(pin, i));
    }
}

void MC14051B::reset()
{
    digitalWrite(controlPin, HIGH);
    delay(10);
    digitalWrite(controlPin, LOW);
}

MC14051B::~MC14051B()
{
    digitalWrite(controlPin, HIGH);
}
