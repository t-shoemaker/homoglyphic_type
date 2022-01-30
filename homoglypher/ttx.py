#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

class Font:
    
    order = {}
    order_rev = {}
    cmap = {}
    chars = []

    def __init__(self, filename):
        with open(filename, 'r') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
            for item in soup.find_all('glyphid'):
                idx = int(item['id'])
                name = item['name']
                self.order[idx] = name
                self.order_rev[name] = idx
                data = soup.find('ttglyph', {'name': name})
                if data:
                    self.chars.append(self.Char(data))
            for item in soup.find_all('map'):
                self.cmap[item['name']] = item['code']
        self.n_char = len(self.cmap)

    def get_component_contours(self, idx):
        char = self.chars[idx]
        if char.components:
            component_contours = []
            for component in char.components:
                name = component['glyphname']
                idx = self.order_rev[name]                
                contours = self.chars[idx].contours
                component_contours.append({
                    'name': name,
                    'position': {
                        'x': component['x'],
                        'y': component['y']
                    },
                    'contours': contours
                })
            return component_contours
        else:
            raise Exception(f"No components for {char.name}")

    class Char:

        def __init__(self, data):
            self.data = data
            self.name = data['name']

        @property
        def bounds(self):
            if list(self.data.children):
                return {
                    'xmax': int(self.data['xmax']),
                    'xmin': int(self.data['xmin']),
                    'ymax': int(self.data['ymax']),
                    'ymin': int(self.data['ymin'])
                }
            else:
                return None

        @property
        def contours(self):
            if self.data.find('contour'):
                contours = []
                for contour in self.data.find_all('contour'):
                    stroke = []
                    points = contour.find_all('pt')
                    for pt in points:
                        stroke.append({
                            'on': pt['on'],
                            'x': pt['x'],
                            'y': pt['y'],
                        })
                    contours.append(stroke)
                return contours
            else:
                return None

        @property
        def n_contours(self):
            if self.contours:
                return len(self.contours)
            else:
                return 0

        @property
        def components(self):
            if self.data.find('component'):
                components = []
                for component in self.data.find_all('component'):
                    components.append({
                        'flags': component['flags'],
                        'glyphname': component['glyphname'],
                        'x': int(component['x']),
                        'y': int(component['y'])
                    })
                return components
            else:
                return None

        @property
        def n_components(self):
            if self.components:
                return len(self.components)
            else:
                return 0

        @property
        def null_char(self):
            if (self.bounds is None) and (self.contours is None) and (self.components is None):
                return True
            else:
                return False
