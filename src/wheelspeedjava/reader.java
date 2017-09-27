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

    private double frontRPMs, rearRPMs, deltaRPMs = 0.0d;
    private int frontCount, rearCount = 0;
    private long nowTime;
    private String updateTime = "12:00:00.000";
    private final SimpleDateFormat clockFormat = new SimpleDateFormat("HH:mm:ss,SSS");
    private final SimpleDateFormat dateFormat = new SimpleDateFormat("YYYY-MM-dd.HHmm");

    public static void main(String[] args) throws Exception {
        new reader().go(args);
    }

    @Override
    protected void run(String[] args) throws IOException {
        // this should be recording GPS, and the printing for RPM should happen in the looper
        while (true) {

            try {
                Thread.sleep(12000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    public String getFrontCount() {
        return Integer.toString(frontCount);
    }

    public String getRearCount() {
        return Integer.toString(rearCount);
    }

    // truncate the fraction 
    public String getRevs(double rpms) {
        String rpm = Double.toString(rpms);
        int point = rpm.indexOf('.');
        if (point > 0) {
            return rpm.substring(0, point);
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
        private WheelRPMcalculator frontRPM;
        private WheelRPMcalculator rearRPM;

        @Override
        public void setup() throws ConnectionLostException {
            updateTime = dateFormat.format(new Date());
            try {
                writer = new FileWriter("PickleData." + updateTime + "hours.log");
                writer.write("Hr:Min:Sec,Millis,FrontCount,RearCount,FrontRPM,RearRPM,DeltaRPM\n");
                writer.flush();
            } catch (Exception e) {
                e.printStackTrace();
            }
            frontReader = new WheelSensorReader(ioio_, WheelSensorReader.frontInput);
            frontReader.start();
            frontRPM = new WheelRPMcalculator();
            rearReader = new WheelSensorReader(ioio_, WheelSensorReader.rearInput);
            rearReader.start();
            rearRPM = new WheelRPMcalculator();
            //write.syslog("Looper setup complete");
        }

        @Override
        public void loop() throws ConnectionLostException, InterruptedException {
            nowTime = System.currentTimeMillis();
            frontCount = frontReader.getCount();
            rearCount = rearReader.getCount();

            // these are doubles
            frontRPMs = frontRPM.getRPM(nowTime, frontCount);
            rearRPMs = rearRPM.getRPM(nowTime, rearCount);
            deltaRPMs = frontRPMs - rearRPMs;

            updateTime = clockFormat.format(nowTime);

            if (frontRPMs > 0.0d || rearRPMs > 0.0d) {
                try {
                    writer.write(updateTime + ","
                            + getFrontCount() + ","
                            + getRearCount() + ","
                            + getRevs(frontRPMs) + ","
                            + getRevs(rearRPMs) + ","
                            + getRevs(deltaRPMs) + "\n");
                    writer.flush();
                } catch (Exception e) {
                    e.printStackTrace();
                }
                Thread.sleep(1000);
            }
        }
    }
}
