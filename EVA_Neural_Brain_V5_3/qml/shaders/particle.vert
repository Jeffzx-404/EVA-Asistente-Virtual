VARYING vec2 uv;
VARYING float seed;
VARYING float emission;
void MAIN() {
    uv = UV0;
    seed = UV1.x;
    emission = .75;
    POSITION = MODELVIEWPROJECTION_MATRIX * vec4(VERTEX, 1.0);
}
