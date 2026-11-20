VARYING vec2 uv;
VARYING float seed;
VARYING float emission;
void MAIN() {
    float radius = dot(uv, uv);
    float core = exp(-radius*32.0);
    float halo = .16*exp(-radius*4.0);
    float star = (exp(-abs(uv.x)*55.0-abs(uv.y)*5.0) +
                  exp(-abs(uv.y)*55.0-abs(uv.x)*5.0)) * .13;
    float shimmer = .6 + .4*sin(uTime*6.28318530718/4096.0*1043.0 + seed*60.0);
    float luminosity = (core + halo + star) * (.9 + shimmer*.9) * emission;
    FRAGCOLOR = vec4(uTint * luminosity * uEnergy, min(1.0, luminosity) * uOpacity);
}
