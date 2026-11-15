from functools import partial as BindResearch

from convert.Commands.MainEntry import MainEntry as RuntimeEntry
from KitCli.RunResearch import RunResearch

# research process access belongs to the explicit developer command composition
MainEntry = BindResearch(RuntimeEntry, ResearchRunner=RunResearch)
