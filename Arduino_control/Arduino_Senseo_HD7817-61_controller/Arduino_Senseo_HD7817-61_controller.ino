/**
 * Senseo coffee maker by Equisense
 */
 
int power_out_pin, short_coffee_out_pin, long_coffee_out_pin, short_coffee_in_pin, long_coffee_in_pin, short_coffee_in, long_coffee_in, push_delay;
void setup() {
  // We set the push delay (delay between the high and low signal)
  push_delay = 100;
  // We set the pins positions
  power_out_pin = 1;
  short_coffee_out_pin  = 2;
  long_coffee_out_pin = 3;
  short_coffee_in_pin = 4;
  long_coffee_in_pin = 5;
  // We init the values of the inputs
  short_coffee_in = 0;
  long_coffee_in = 0;
  // We init the in/out pins
  pinMode(power_out_pin, OUTPUT);
  pinMode(short_coffee_out_pin, OUTPUT);
  pinMode(long_coffee_out_pin, OUTPUT);
  pinMode(short_coffee_in_pin, INPUT);
  pinMode(long_coffee_in_pin, INPUT);
}

void loop() {
  short_coffee_in = digitalRead(short_coffee_in_pin);
  long_coffee_in = digitalRead(long_coffee_in_pin);
  if(short_coffee_in || long_coffee_in){
    digitalWrite(power_out_pin, HIGH); 
    delay(push_delay);              // wait for a second
    digitalWrite(power_out_pin, LOW);
    delay(10000);              // wait for 10 seconds
    digitalWrite(short_coffee_out_pin, short_coffee_in);
    digitalWrite(long_coffee_out_pin, long_coffee_in);
    delay(push_delay);
    digitalWrite(short_coffee_out_pin, LOW);
    digitalWrite(long_coffee_out_pin, LOW);
  }
}
