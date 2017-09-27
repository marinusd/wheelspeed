package wheelspeedjava;

import ioio.lib.api.DigitalInput;
import ioio.lib.api.IOIO;
import ioio.lib.api.exception.ConnectionLostException;
import ioio.lib.util.BaseIOIOLooper;
import ioio.lib.util.IOIOConnectionManager.Thread;
import ioio.lib.util.IOIOLooper;
import ioio.lib.util.pc.IOIOConsoleApp;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.text.SimpleDateFormat;
import java.util.Date;

public class reader extends IOIOConsoleApp {

    private double frontRPMs, rearRPMs, deltaRPMs = 0.0d;
    private int frontCount, rearCount = 0;
    private long nowTime;
    private String updateTime = "12:00:00.000";
    private final SimpleDateFormat clockFormat = new SimpleDateFormat("HH:mm:ss.SSS");

    public static void main(String[] args) throws Exception {
        new reader().go(args);
    }

    @Override
    protected void run(String[] args) throws IOException {
        // this should be recording GPS, and the printing for RPM should happen in the looper
        System.out.println("data,TIME,F.CT,F.RPM,R.CT,R.RPM,D.RPM");
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
            return rpm.substring(0,point);
        }
        return rpm;
    }

    @Override
    public IOIOLooper createIOIOLooper(String connectionType, Object extra) {
        return new Looper();
    }

    private class Looper extends BaseIOIOLooper {
        private WheelSensorReader frontReader;
        private WheelSensorReader rearReader;
        private WheelRPMcalculator frontRPM;
        private WheelRPMcalculator rearRPM;

        @Override
        public void setup() throws ConnectionLostException {
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
            System.out.println("data,"
                    + updateTime + ","
                    + getFrontCount() + ","
                    + getRevs(frontRPMs) + ","
                    + getRearCount() + ","
                    + getRevs(rearRPMs) + ","
                    + getRevs(deltaRPMs));
            }
            /* only log if we're moving
             if (!lastLat.equals(latitude) ||
             !lastLong.equals(longitude) || 
             !lastSpeed.equals(speed) )  {
             // log the data
             // "SYSTIME,LH,RH,GPSTIME,LAT,LONG,DIST,SPEED,F.RPM,D.RPM,R.RPM";
             write.data(updateTime + "," + leftReading + "," + rightReading
             + "," + gpsTime + "," + latitude + "," + longitude
             + "," + distFromStart + "," + speed + "," + frontRevs
             + "," + deltaRevs + "," + rearRevs);

             }
             */

            Thread.sleep(1000);
        }
    }
}
