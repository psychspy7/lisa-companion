shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, depth_draw_opaque;
uniform sampler2D artwork : source_color, filter_linear_mipmap, repeat_disable;
uniform vec4 frame_rect = vec4(0.0,0.0,1.0,1.0);
uniform bool mirror = false;
uniform bool face_enabled = false;
uniform float voice = 0.0;
uniform float blink = 0.0;
uniform float opacity = 1.0;
void fragment(){
 vec2 p = UV;
 if(mirror){p.x = 1.0-p.x;}
 vec2 sample_uv = frame_rect.xy+p*frame_rect.zw;
 vec4 pixel = texture(artwork,sample_uv);
 vec3 color = pixel.rgb;
 if(face_enabled){
  vec2 lip = vec2(0.50,0.137);
  float opening = 0.0018+clamp(voice,0.0,1.0)*0.0075;
  float mouth = 1.0-smoothstep(0.80,1.15,length((p-lip)/vec2(0.022,opening)));
  color = mix(color,vec3(0.17,0.035,0.050),mouth*clamp(voice*4.0,0.0,0.95));
  float eye_left = 1.0-smoothstep(0.8,1.1,length((p-vec2(0.422,0.102))/vec2(0.038,0.012)));
  float eye_right = 1.0-smoothstep(0.8,1.1,length((p-vec2(0.565,0.102))/vec2(0.038,0.012)));
  vec3 skin = texture(artwork,frame_rect.xy+vec2(p.x,p.y+0.017)*frame_rect.zw).rgb;
  color = mix(color,skin,max(eye_left,eye_right)*blink);
  float lid = (1.0-smoothstep(0.0008,0.0025,abs(p.y-0.102)))*step(abs(p.x-0.422),0.032);
  lid = max(lid,(1.0-smoothstep(0.0008,0.0025,abs(p.y-0.102)))*step(abs(p.x-0.565),0.032));
  color = mix(color,vec3(0.12,0.03,0.025),lid*blink);
 }
 ALBEDO = color;
 ALPHA = pixel.a*opacity;
 ALPHA_SCISSOR_THRESHOLD = 0.10;
}
