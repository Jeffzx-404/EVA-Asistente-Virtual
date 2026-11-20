VARYING vec3 worldNormal;
VARYING vec3 viewDirection;
VARYING vec3 localPosition;
void MAIN() {
    worldNormal = normalize(NORMAL_MATRIX * NORMAL);
    viewDirection = CAMERA_POSITION - (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    localPosition = VERTEX;
    POSITION = MODELVIEWPROJECTION_MATRIX * vec4(VERTEX, 1.0);
}
