package wheelspeedjava;

import ioio.lib.api.IOIO;
import ioio.lib.api.DigitalInput;
import ioio.lib.api.PulseInput;

public class WheelSensorReader {
    public static int frontInput = 11;
    public static int rearInput  = 13;
    private float rpm = 0f;
    private PulseInput pulse;

    float getRPM() {
        rpm = 0f;
        try {
            rpm = pulse.getFrequency() * 60f;  // getFrequency() gives a float
        } catch (Exception e) {
            e.printStackTrace();
        }
        return rpm;
    }

    WheelSensorReader(IOIO ioio_, int pin) {
        DigitalInput.Spec pinSpec = new DigitalInput.Spec(pin,DigitalInput.Spec.Mode.PULL_UP);
        PulseInput.ClockRate rate = PulseInput.ClockRate.RATE_2MHz;
        PulseInput.PulseMode freq = PulseInput.PulseMode.FREQ; //_SCALE_4;
        boolean doublePrecision = true;
        System.out.println("WheelSensorReader is being created for pin " + pin);
        try {
            pulse = ioio_.openPulseInput(pinSpec, rate, freq, doublePrecision);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}
