VARYING vec2 uv;
VARYING float seed;
VARYING float depthLight;
VARYING float nearBrain;
VARYING float visibility;
void MAIN() {
    uv = UV0;
    seed = UV1.x;
    float phase = uTime*6.28318530718/4096.0;
    float layer = smoothstep(-260.0,210.0,VERTEX.z);
    float speed = 12.0 + floor(seed*16.0+layer*12.0);
    vec3 drift = vec3(
        sin(phase*speed + seed*51.0),
        cos(phase*(speed+7.0) + seed*29.0),
        sin(phase*(speed+13.0) + seed*37.0));
    drift *= 2.5 + seed*4.0;
    vec3 center = VERTEX + drift;
    center.xy += (uParallax + vec2(sin(phase*47.0),cos(phase*53.0))*2.0)*layer;
    // La cámara mira hacia -Z y este modelo no rota: XY es su plano frontal.
    // Una única matriz MVP conserva la corrección de proyección del backend RHI.
    vec3 corner = center + vec3(UV0 * UV1.y*(.65+.35*layer), 0.0);
    POSITION = MODELVIEWPROJECTION_MATRIX * vec4(corner, 1.0);
    depthLight = clamp(620.0 / max(600.0-center.z, 120.0), .45, 1.3);
    nearBrain = 1.0-smoothstep(210.0, 285.0, length(center));
    vec4 projected = MODELVIEWPROJECTION_MATRIX * vec4(center,1.0);
    vec2 screen = projected.xy/projected.w;
    // Atenuar puntos sobre la silueta central y cerca de los límites del viewport.
    visibility = mix(.18,1.0,smoothstep(.25,.55,length(screen*vec2(1.3,1.0))));
    visibility *= 1.0-smoothstep(.82,.98,abs(screen.y));
}
