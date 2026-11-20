VARYING vec3 worldNormal;
VARYING vec3 viewDirection;
VARYING vec3 localPosition;
void MAIN() {
    float rim = pow(1.0-abs(dot(normalize(worldNormal), normalize(viewDirection))), 9.0);
    float latitude = pow(.5+.5*sin(localPosition.y*1.65), 30.0);
    float brightness = .45 + .12 * sin(uTime*6.28318530718/4096.0*261.0 + localPosition.y*.04);
    FRAGCOLOR = vec4(uTint * (brightness + rim), rim*.10 + latitude*.001);
}
