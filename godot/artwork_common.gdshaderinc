uniform sampler2D artwork : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D previous_artwork : source_color, filter_linear_mipmap, repeat_disable;
uniform vec4 frame_rect = vec4(0.0,0.0,1.0,1.0);
uniform vec4 previous_rect = vec4(0.0,0.0,1.0,1.0);
uniform vec4 top_region = vec4(0.12,0.19,0.76,0.30);
uniform bool mirror = false;
uniform bool face_enabled = false;
uniform float voice = 0.0;
uniform float blink = 0.0;
uniform float opacity = 1.0;
uniform float pose_mix = 1.0;
uniform float gesture = 0.0;
uniform float motion_amount = 1.0;
uniform float exercise = 0.0;
uniform float outfit = 0.0;
// Small anchored deformations in metres. Legs are never rotated over the head.
void vertex(){
 float arm = smoothstep(0.20,0.43,abs(UV.x-0.5));
 arm *= smoothstep(0.17,0.28,UV.y)*(1.0-smoothstep(0.60,0.72,UV.y));
 float side = UV.x>0.5 ? 1.0 : -1.0;
 VERTEX.x += side*arm*0.026*sin(TIME*3.1+side)*gesture*motion_amount;
 VERTEX.y += arm*0.019*sin(TIME*2.7+side)*gesture*motion_amount;
 float head = 1.0-smoothstep(0.18,0.27,UV.y);
 VERTEX.x += head*0.008*sin(TIME*1.4)*gesture*motion_amount;
 float torso = smoothstep(0.18,0.25,UV.y)*(1.0-smoothstep(0.44,0.52,UV.y));
 VERTEX.y += torso*0.004*sin(TIME*1.9)*motion_amount;
 VERTEX.y -= 0.018*(0.5+0.5*sin(TIME*2.2))*exercise*motion_amount;
}
vec4 sample_frame(sampler2D tex,vec4 rect,vec2 p){
 return texture(tex,rect.xy+p*rect.zw);
}
void fragment(){
 vec2 p = UV;
 if(mirror){p.x=1.0-p.x;}
 vec4 pixel = sample_frame(artwork,frame_rect,p);
 if(pose_mix<1.0){pixel=mix(sample_frame(previous_artwork,previous_rect,p),pixel,pose_mix);}
 vec3 color = pixel.rgb;
 // Second coordinated outfit look. Keep skin and red hair unchanged.
 vec2 region = (p-top_region.xy)/top_region.zw;
 float cloth = step(0.0,region.x)*step(region.x,1.0)*step(0.0,region.y)*step(region.y,1.0);
 float dark = 1.0-smoothstep(0.14,0.30,max(max(color.r,color.g),color.b));
 float neutral = 1.0-smoothstep(0.025,0.09,abs(color.r-color.g)+abs(color.g-color.b));
 color += vec3(0.12,0.016,0.033)*cloth*dark*neutral*outfit;
 if(face_enabled && pose_mix>0.95){
  float opening = 0.0018+clamp(voice,0.0,1.0)*0.0075;
  float mouth = 1.0-smoothstep(0.8,1.15,length((p-vec2(0.5,0.137))/vec2(0.022,opening)));
  color = mix(color,vec3(0.17,0.035,0.05),mouth*clamp(voice*4.0,0.0,0.95));
  float eyes = max(1.0-smoothstep(0.8,1.1,length((p-vec2(0.422,0.102))/vec2(0.038,0.012))),1.0-smoothstep(0.8,1.1,length((p-vec2(0.565,0.102))/vec2(0.038,0.012))));
  vec3 skin = sample_frame(artwork,frame_rect,vec2(p.x,p.y+0.017)).rgb;
  color = mix(color,skin,eyes*blink);
  float lid = (1.0-smoothstep(0.0008,0.0025,abs(p.y-0.102)))*max(step(abs(p.x-0.422),0.032),step(abs(p.x-0.565),0.032));
  color = mix(color,vec3(0.12,0.03,0.025),lid*blink);
 }
 ALBEDO=color; ALPHA=pixel.a*opacity; ALPHA_SCISSOR_THRESHOLD=0.10;
}
