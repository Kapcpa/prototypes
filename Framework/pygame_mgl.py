import moderngl
import pygame

from array import array


def read_f(path):
    f = open(path, 'r')
    dat = f.read()
    f.close()
    return dat


class MGL:
    def __init__(self):
        self.ctx = moderngl.create_context()
        self.textures = {}
        self.programs = {}
        self.quad_buffer = self.ctx.buffer(data=array('f', [
            # position (x, y) , texture coordinates (x, y)
            -1.0, 1.0, 0.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 0.0,
            1.0, -1.0, 1.0, 1.0,
        ]))
        self.vaos = {}

        self.initialize()

    def initialize(self):
        # Set shaders for all different textures that will be used
        self.compile_program('default', 'default', 'default')

        self.compile_program('default', 'game_display', 'game_display')

        self.compile_program('default', 'vignette', 'vignette')
        self.compile_program('default', 'gblur_shader', 'gblur_layer')

        # Initialize static textures
        self.load_texture('noise', 'Data/Sprites/Misc', False)

    def render(self, game_config={}):
        self.ctx.clear(0.47843, 0.28235, 0.2549)

        self.ctx.enable(moderngl.BLEND)

        # Dont draw anything if there isnt base_display texture made
        if 'base_display' in self.textures:
            # Pass here all uniforms used in specific .frag shader

            self.update_render('game_display', {
                'surface': self.textures['base_display'],
                'ground_surface': self.textures['ground_layer'],
                'map_surface': self.textures['map_surface'],
                'silhouette_surface': self.textures['silhouette_surface'],

                'shadow_noise': self.textures['noise'],

                'rgb_split': game_config['rgb_split'],

                'shockwaves': game_config['shockwaves'],
                'shockwaves_count': len(game_config['shockwaves']),

                'edges': game_config['edges'],
                'edges_count': game_config['edges_count'],
                'player_pos': game_config['player_pos'],

                'screen_res': game_config['screen_res'],
                'scroll': game_config['scroll'],

                'chase': game_config['chase'],
                'chase_lights': game_config['chase_lights'],

                'view_dist': game_config['view_dist']
            })

            if game_config['gblur_render'] and 'gblur_layer' in self.textures:
                self.update_render('gblur_layer', {
                    'surface': self.textures['gblur_layer'],
                    'horizontal': True
                })
                self.update_render('gblur_layer', {
                    'surface': self.textures['gblur_layer'],
                    'horizontal': False,
                })

            self.update_render('vignette', {
                'ui_surface': self.textures['ui_display'],

                'blood_visibility': game_config['blood_visibility'],

                'player_pos': game_config['player_pos'],

                'screen_res': game_config['screen_res'],
                'scroll': game_config['scroll'],

                'vignette_strength': game_config['vignette_strength'],
                'flash_time': game_config['flash_time'],
                'scene_fade': game_config['scene_fade']
            })

        if game_config['pause'] or game_config['loading']:
            self.update_render('default', {'surface': self.textures['pause_display']})

        self.ctx.disable(moderngl.BLEND)

    def update_render(self, program_name, uniforms):
        self.update_shader(program_name, uniforms)
        self.vaos[program_name].render(mode=moderngl.TRIANGLE_STRIP)

    def update_shader(self, program_name, uniforms):
        tex_id = 0
        for uniform in uniforms:
            if type(uniforms[uniform]) == moderngl.Texture:
                uniforms[uniform].use(tex_id)
                self.programs[program_name][uniform].value = tex_id
                tex_id += 1
            else:
                self.programs[program_name][uniform].value = uniforms[uniform]

    def compile_program(self, vert_src, frag_src, program_name):
        vert_raw = read_f('Data/Shaders/' + vert_src + '.vert')
        frag_raw = read_f('Data/Shaders/' + frag_src + '.frag')
        program = self.ctx.program(vertex_shader=vert_raw, fragment_shader=frag_raw)
        self.programs[program_name] = program
        self.vaos[program_name] = self.ctx.vertex_array(program, [(self.quad_buffer, '2f 2f', 'in_vert', 'in_texcoord')])

    def load_texture(self, name, loc, alpha=True):
        if not alpha:
            surf = pygame.image.load(loc + '/' + name + '.png').convert()
        else:
            surf = pygame.image.load(loc + '/' + name + '.png')

        self.pg2tx(surf, name)

    def pg2tx(self, surface, texture_name):
        channels = 4
        if texture_name not in self.textures:
            new_tex = self.ctx.texture(surface.get_size(), channels)
            new_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            new_tex.swizzle = 'BGRA'
            self.textures[texture_name] = new_tex

        texture_data = surface.get_view('1')
        self.textures[texture_name].write(texture_data)
