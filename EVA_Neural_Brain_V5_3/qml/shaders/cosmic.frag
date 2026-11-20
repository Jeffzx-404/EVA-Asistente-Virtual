VARYING vec2 uv;
VARYING float seed;
VARYING float depthLight;
VARYING float nearBrain;
VARYING float visibility;
void MAIN() {
    float r = dot(uv, uv);
    float phase = uTime*6.28318530718/4096.0;
    float twinkle = pow(.5+.5*sin(phase*(93.0+floor(seed*60.0))+seed*57.0), 8.0);
    vec3 natural = seed < .33 ? vec3(.32,.48,1.0) :
                   (seed < .70 ? vec3(.55,.32,1.0) : vec3(.7,.78,1.0));
    vec3 tint = mix(natural, uTint, nearBrain*.8);
    float light = (exp(-r*32.0)+.09*exp(-r*3.0))*(.55+twinkle*.95)*depthLight*visibility;
    FRAGCOLOR = vec4(tint*light*3.0, clamp(light,0.0,1.0)*.7);
}
