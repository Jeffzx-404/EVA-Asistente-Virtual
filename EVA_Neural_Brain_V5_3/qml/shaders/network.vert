VARYING vec2 trace;
void MAIN() {
    trace = UV0;
    POSITION = MODELVIEWPROJECTION_MATRIX * vec4(VERTEX, 1.0);
}
