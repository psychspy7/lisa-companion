#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf { mat4 qt_Matrix; float qt_Opacity; } ubuf;
layout(binding = 1) uniform sampler2D source;
void main() {
    vec4 c=texture(source,qt_TexCoord0);
    float dominance=c.g-max(c.r,c.b);
    float key=smoothstep(0.10,0.30,dominance)*smoothstep(0.24,0.48,c.g);
    c.g=min(c.g,max(c.r,c.b)+0.06);
    fragColor=c*(1.0-key)*ubuf.qt_Opacity;
}
