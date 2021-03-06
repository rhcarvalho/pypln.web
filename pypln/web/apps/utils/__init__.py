# coding: utf-8
#
# Copyright 2012 NAMD-EMAP-FGV
#
# This file is part of PyPLN. You can get more information at: http://pypln.org/.
#
# PyPLN is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyPLN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyPLN.  If not, see <http://www.gnu.org/licenses/>.


from .tagset import TAGSET, COMMON_TAGS
from .languages import LANGUAGES
from .pipeline import create_pipelines, get_config_from_router

from django.template.defaultfilters import slugify

def slugify_keeping_dots(filename):
    slug = '.'.join([slugify(x) for x in filename.split('.')])
    # gridfs uses _ instead of -
    return slug.replace('-', '_')
