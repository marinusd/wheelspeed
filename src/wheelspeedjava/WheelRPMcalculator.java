package wheelspeedjava;

class WheelRPMcalculator {
    private int lastCount, revolutions;
    private long lastTime, elapsedTime;
    private double seconds, rpm;

    WheelRPMcalculator(){
        lastCount = 0;
        lastTime = System.currentTimeMillis();
    }
    
    double getRPM(long nowTime, int count) {
        elapsedTime = nowTime - lastTime;
        lastTime = nowTime;

        revolutions = count - lastCount;
        lastCount = count;

        seconds = elapsedTime/1000.0d;
        rpm = revolutions / seconds * 60;

        return rpm;

    }
}