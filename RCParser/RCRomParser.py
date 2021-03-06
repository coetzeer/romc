# -*- coding: utf-8 -*-

import re

from RCUtils import *
from RCReport import RCReport
from RCGameParser import RCGameParser

class RCRomParser(RCGameParser):
	""" Parser pour système console """

	regex = ur'(?<!\w)\(?(?P<special>BIOS|BS|PC10|ST|NP|HWTests)\)?(?!\w)|(?:\(V *(?P<version>[\d.]+)\))|(?:\((?P<field>(?:[\w\s.&\'-]+ )?(?P<hack1>Hack)(?: [\w\s.&\'-]*)?|(?:(?P<media>Cart|Disc|Disk|Tape) *(?P<media_n>\d+)(?: *Side *(?P<side>A|B))?)|[\w\s]+)\))|(?:__(?P<flags>(?P<good>!)|(?:(?P<fixe>f)|(?P<hack2>h|p))[ _]*(?P<flag_version>[\d\w]+)?|.+?)__)'
	
	def __init__(self, games_list, config, system, hyperpause=False, csv=None, strl=0, strl_suffix='', csv_no_info_str=''):
		super(RCRomParser, self).__init__(games_list, config, system, hyperpause=hyperpause, csv=csv, strl=strl, strl_suffix=strl_suffix, csv_no_info_str=csv_no_info_str)
		self.move_temp_games = True
		self.ok_flags           = config.get(system, 'flags').split(',')
	
	def _first_stage(self):
		report = RCReport()
		regex  = re.compile(RCRomParser.regex, re.IGNORECASE)
		
		for (game_name, game_file) in self.list.items():
			filename  = game_name
			game_name = clean_filename(game_name)
			
			country  = None
			version  = None
			hack     = None
			good     = None
			fixe     = None
			special  = None
			flag_ver = None
			flags    = None
			media    = None
			media_n  = None
			side     = None
			ok_flags = None
			
			move = False
			
			report.log('\t' + game_name, 2)
			
			for field in regex.finditer(game_name):
				temp_country = field.group('field')
				temp_flags   = field.group('flags')
				
				version  = version  or field.group('version')
				hack     = hack     or field.group('hack1') or field.group('hack2')
				good     = good     or field.group('good')
				fixe     = fixe     or field.group('fixe')
				special  = special  or field.group('special')
				flag_ver = flag_ver or field.group('flag_version')
				media    = media    or field.group('media')
				media_n  = media_n  or (int(field.group('media_n')) if field.group('media_n') != None else None)
				side     = side     or field.group('side')
				
				if temp_country in self.countries or temp_country in self.exclude_countries:
					country = country or temp_country
				
				if temp_flags in self.ok_flags and flags == None:
					ok_flags = ok_flags or temp_flags
				else:
					flags    = temp_flags
					ok_flags = None
			
			# On conserve que les meilleures dump
			if special != None and not self.config.get(self.system, 'special'):
				report.log('\t\t- Special game not allowed (' + special + ')', 3)
				move = True
			elif media_n != None and media_n > 1:
				report.log('\t\t- Not the first media (' + str(media_n) + ')', 3)
				continue # On ne déplace pas le jeu, celui-ci doit rester dans le dossier.
			# Si c'est un hack, on vérifie si on les autorise
			elif hack != None and self.config.get(self.system, 'only_legit'):
				report.log('\t\t- Not legit', 3)
				move = True
			# Si il y a n'importe quel autre flag, on ne garde pas
			elif good == None and fixe == None and ok_flags == None and flags != None:
				report.log('\t\t- Bad dump', 3)
				move = True
			# On vérifie si on autorise le pays.
			elif country == None and not self.config.get(self.system, 'allow_no_country'):
				report.log('\t\t- Country not found', 3)
				move = True
			elif country != None and country in self.exclude_countries:
				report.log('\t\t- Excluded country (' + country + ')', 3)
				move = True
			
			# On déplace le jeu si besoin
			if move:
				self.move_games.append(game_name)
				continue
			
			# Nettoyage du nom du jeu
			game_clean_name = clean_name(game_name) if not hack else game_name
			
			# Ajout du jeu dans la liste temporaire
			if game_clean_name not in self.temp_games:
				self.temp_games[game_clean_name] = []
			
			self.temp_games[game_clean_name].append({
				'original_name': filename,
				'game_name':     game_name,
				'country':       country,
				'version':       norm_version(version),
				'editor':        None,
				'year':          None,
				'genre':         None,
				'resume':        None,
				'note':          None,
				'rating':        None,
				'score':         100 if flags == None or hack != None else self._calc_flag_score(good, fixe, flag_ver),
				'onlineData':    { 'state': False }
			})
			
			report.log('\t\t+ Preselected game. Clean name : ' + game_clean_name, 2)
	
	def _calc_flag_score(self, good, fixe, flag_ver):
		score = 0
		
		score += 100 if good else 0
		score += 1 if fixe else 0
		score += int(flag_ver) if flag_ver else 0
		
		return score
