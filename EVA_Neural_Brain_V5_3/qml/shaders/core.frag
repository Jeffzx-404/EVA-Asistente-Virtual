VARYING vec2 trace;
void MAIN() {
    vec2 uv = trace*2.0-1.0;
    float pulse = .8+.2*sin(uTime*6.28318530718/4096.0*652.0);
    float light = exp(-dot(uv,uv)*4.2);
    FRAGCOLOR = vec4(uTint*light*.55*(1.0+.25*uSpeechLevel), light*.16*pulse);
}
