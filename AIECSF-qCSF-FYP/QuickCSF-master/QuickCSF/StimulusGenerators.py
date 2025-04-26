'''Classes to generate stimuli for testing'''

import random

import numpy

from . import QuickCSF
from . import gaborPatch

class Stimulus:
	def __init__(self, contrast, frequency, orientation, size):
		self.contrast = contrast
		self.frequency = frequency
		self.orientation = orientation
		self.size = size

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f'c={self.contrast},f={self.frequency},o={self.orientation},s={self.size}'

class QuickCSFGenerator(QuickCSF.QuickCSFEstimator):
	''' Generate fixed-size stimuli with contrast/spatial frequency determined by QuickCSF

		If orientation is None, random orientations will be generated
	'''

	def __init__(self,
		size=100, orientation=None,
		minContrast=.01, maxContrast=1.0, contrastResolution=24,
		minFrequency=0.2, maxFrequency=36.0, frequencyResolution=20,
		degreesToPixels=None
	):
		self._initial_params = {
			'size': size,
			'orientation': orientation,
			'minContrast': minContrast,
			'maxContrast': maxContrast,
			'contrastResolution': contrastResolution,
			'minFrequency': minFrequency,
			'maxFrequency': maxFrequency,
			'frequencyResolution': frequencyResolution,
		}
		
		self.size = size
		self.orientation = orientation
		
		if degreesToPixels is None:
			self.degreesToPixels = lambda x: x
		else:
			self.degreesToPixels = degreesToPixels

		# Initialize QuickCSFEstimator with stimulus space
		QuickCSF.QuickCSFEstimator.__init__(
			self,
			stimulusSpace = [
				QuickCSF.makeContrastSpace(minContrast, maxContrast, contrastResolution),
				QuickCSF.makeFrequencySpace(minFrequency, maxFrequency, frequencyResolution)
			 ]
		)

	def reset(self):
		"""Reset generator to initial state"""
		self.size = self._initial_params['size']
		self.orientation = self._initial_params['orientation']
		
		# Reset the stimulus space directly without calling parent's __init__
		self.stimulusSpace = [
			QuickCSF.makeContrastSpace(
				self._initial_params['minContrast'],
				self._initial_params['maxContrast'],
				self._initial_params['contrastResolution']
			),
			QuickCSF.makeFrequencySpace(
				self._initial_params['minFrequency'],
				self._initial_params['maxFrequency'],
				self._initial_params['frequencyResolution']
			)
		]
		QuickCSF.QuickCSFEstimator.reset(self)

	def next(self):
		stimulus = super().next()

		if self.orientation is None:
			orientation = random.random() * 360
		else:
			orientation = self.orientation

		return gaborPatch.ContrastGaborPatchImage(
			size=self.degreesToPixels(self.size),
			contrast=stimulus.contrast,
			frequency=1/self.degreesToPixels(1/stimulus.frequency),
			orientation=orientation
		)
