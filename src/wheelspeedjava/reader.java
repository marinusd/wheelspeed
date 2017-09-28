package wheelspeedjava;

import ioio.lib.api.exception.ConnectionLostException;
import ioio.lib.util.BaseIOIOLooper;
import ioio.lib.util.IOIOConnectionManager.Thread;
import ioio.lib.util.IOIOLooper;
import ioio.lib.util.pc.IOIOConsoleApp;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class reader extends IOIOConsoleApp {

    private float frontRPMs, rearRPMs, deltaRPMs = 0.0f;
    private long nowTime;
    private String updateTime = "12:00:00.000";
    private final SimpleDateFormat clockFormat = new SimpleDateFormat("HH:mm:ss,SSS");
    private final SimpleDateFormat dateFormat = new SimpleDateFormat("YYYY-MM-dd.HHmm");

    public static void main(String[] args) throws Exception {
        new reader().go(args);
    }

    @Override
    protected void run(String[] args) throws IOException {
        // this should be doing Screen Display for speed and rear rpm?
        // recording GPS and RPM should happen in the looper
        while (true) {
            if (frontRPMs > 0f || rearRPMs > 0f) {
                System.out.println("==========" + updateTime + "===========\n"
                        + "Front: " + getRevs(frontRPMs) + "\n"
                        + "Rear: " + getRevs(rearRPMs) + ",\n"
                        + "Delta: " + getRevs(deltaRPMs));
            }
            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    // include only the tenths of the fraction 
    public String getRevs(float rpms) {
        String rpm = Float.toString(rpms);
        int point = rpm.indexOf('.');
        if (point > 0) {
            rpm = rpm.substring(0, point + 2);
        }
        return rpm;
    }

    @Override
    public IOIOLooper createIOIOLooper(String connectionType, Object extra) {
        return new Looper();
    }

    private class Looper extends BaseIOIOLooper {

        private FileWriter writer;
        private WheelSensorReader frontReader;
        private WheelSensorReader rearReader;

        @Override
        public void setup() throws ConnectionLostException {
            updateTime = dateFormat.format(new Date());
            try {
                writer = new FileWriter("PickleData." + updateTime + "hours.csv");
                writer.write("Hr:Min:Sec,Millis,FrontRPM,RearRPM,DeltaRPM\n");
                writer.flush();
            } catch (Exception e) {
                e.printStackTrace();
            }
            frontReader = new WheelSensorReader(ioio_, WheelSensorReader.frontInput);
            rearReader = new WheelSensorReader(ioio_, WheelSensorReader.rearInput);
            System.out.println("Looper setup complete");
        }

        @Override
        public void loop() throws ConnectionLostException, InterruptedException {
            nowTime = System.currentTimeMillis();
            updateTime = clockFormat.format(nowTime);

            // these are floats
            frontRPMs = frontReader.getRPM();
            rearRPMs = rearReader.getRPM();
            deltaRPMs = frontRPMs - rearRPMs;

            if (frontRPMs > 0f || rearRPMs > 0f) {
                try {
                    writer.write(updateTime + ","
                            + getRevs(frontRPMs) + ","
                            + getRevs(rearRPMs) + ","
                            + getRevs(deltaRPMs) + "\n");
                    writer.flush();
                } catch (Exception e) {
                    e.printStackTrace();
                }
                Thread.sleep(500);
            }
        }
    }
}
