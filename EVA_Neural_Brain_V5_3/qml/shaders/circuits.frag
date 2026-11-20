VARYING vec2 trace;
void MAIN() {
    // Mismas líneas estáticas; pulsos suaves, secundarios respecto de la corteza.
    float phase = uTime*6.28318530718/4096.0;
    float travel = fract(trace.x-uTime/4096.0*floor(uSpeed*4096.0+.5)+trace.y);
    float distance = min(travel,1.0-travel);
    float pulse = exp(-distance*distance*1400.0);
    float extra = fract(trace.x-uTime/4096.0*1423.0+trace.y*2.0);
    pulse += uProcessing*.3*exp(-pow(min(extra,1.0-extra),2.0)*1100.0);
    float receptive = 1.0 + uListening*.07*sin(phase*239.0+trace.y*5.0);
    float speaking = mix(1.0,.88+.12*sin(phase*1173.0-trace.x*3.0),uSpeaking);
    vec3 tint = mix(uTint,uSecondary,clamp(trace.y*.25,0.0,.25));
    float light = (uBase+pulse*uEnergy)*receptive*speaking*(1.0-.65*uStandby);
    FRAGCOLOR = vec4(tint*light,uOpacity);
}
