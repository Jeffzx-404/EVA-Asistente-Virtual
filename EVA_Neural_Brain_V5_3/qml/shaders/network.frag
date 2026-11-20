VARYING vec2 trace;
void MAIN() {
    float travel = fract(trace.x - uTime / 4096.0 * floor(uSpeed*4096.0+.5) + trace.y);
    float distance = min(travel, 1.0-travel);
    float pulse = exp(-distance * distance * 1800.0);
    float sequence = fract(trace.x-uTime/4096.0*1423.0+trace.y*2.0);
    float regionPulse = exp(-pow(min(sequence,1.0-sequence),2.0)*1100.0);
    pulse += uProcessing*regionPulse*.55;
    float emission = .7+.3*sin(uTime*6.28318530718/4096.0*1173.0-trace.x*3.0);
    float shimmer = .7 + .3 * sin(uTime * 6.28318530718/4096.0 * 782.0 + trace.y * 30.0);
    vec3 tint = mix(uTint, uSecondary, trace.y * .4);
    FRAGCOLOR = vec4(tint * (uBase + pulse * uEnergy) * shimmer
                    * mix(1.0,emission,uSpeaking)*(1.0-.65*uStandby), uOpacity);
}
