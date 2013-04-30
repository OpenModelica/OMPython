''' 
Copyright (C) 2011-2012 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.), 
Institute of System Dynamics and Control
All rights reserved.

This file is part of PySimulator.

PySimulator is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySimulator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with PySimulator. If not, see www.gnu.org/licenses.
'''

'''
Created on 05.07.2012

@author: hart_st
'''


# Major library imports
from numpy import array, asarray

# Enthought library imports
from enable.api import ColorTrait, MarkerTrait
from traits.api import Float, Int, Str, Trait

# Local, relative imports
from chaco.abstract_overlay import AbstractOverlay
from chaco.scatterplot import render_markers
from chaco.data_label import DataLabel
from chaco.tools.data_label_tool import DataLabelTool
import numpy

class myScatterInspectorOverlay(AbstractOverlay):
    """
    Highlights points on a scatterplot as the mouse moves over them.
    Can render the points in a different style, as well as display a
    DataLabel.

    Used in conjuction with ScatterInspector.
    """
    
    # The style to use when a point is hovered over
    hover_metadata_name = Str('hover')
    hover_marker = Trait(None, None, MarkerTrait)
    hover_marker_size = Trait(None, None, Int)
    hover_line_width = Trait(None, None, Float)
    hover_color = Trait(None, None, ColorTrait)
    hover_outline_color = Trait(None, None, ColorTrait)

    # The style to use when a point has been selected by a click
    selection_metadata_name = Str('selections')
    selection_marker = Trait(None, None, MarkerTrait)
    selection_marker_size = Trait(None, None, Int)
    selection_line_width = Trait(None, None, Float)
    selection_color = Trait(None, None, ColorTrait)
    selection_outline_color = Trait(None, None, ColorTrait)
    
    stateNames = []
    eigenVectors = None
    
    frequencies = None
    damping = None
    observability = None
    controllability = None
    
    
    label = None    #Label with information
    hasOverlay = []
    labelIndex = [] #index where the label is actually
    oldIndex = array([])
    # For now, implement the equivalent of this Traits 3 feature manually
    # using a series of trait change handlers (defined at the end of the
    # class)
    #@on_trait_change('component.index.metadata_changed,component.value.metadata_changed')
    def metadata_changed(self, object, name, old, new):
        
        if self.component is not None:
            self.component.request_redraw()
        return


    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        plot = self.component
        if not plot or not plot.index or not getattr(plot, "value", True):
            return
        prefix =""
        for inspect_type in (self.hover_metadata_name, self.selection_metadata_name):
            #print " hover on/off1"
            #Hartweg: 2. Bedingung zugefuegt
            if inspect_type in plot.index.metadata:
                
                if hasattr(plot,"value") and not inspect_type in plot.value.metadata:
                    continue
                index = plot.index.metadata.get(inspect_type, None)
                
                if index is not None and len(index) > 0:
                    index = asarray(index)
                    index_data = plot.index.get_data()

                    # Only grab the indices which fall within the data range.
                    index = index[index < len(index_data)]
                    
                    # FIXME: In order to work around some problems with the
                    # selection model, we will only use the selection on the
                    # index.  The assumption that they are the same is
                    # implicit, though unchecked, already.
                    #value = plot.value.metadata.get(inspect_type, None)
                    value = index

                    if hasattr(plot, "value"):
                        value_data = plot.value.get_data()
                        screen_pts = plot.map_screen(array([index_data[index],
                                                            value_data[value]]).T)
                        #print "1 ", array([index_data[index], value_data[value]])
                    else:
                        screen_pts = plot.map_screen(index_data[index])
                        #print "2 ", index_data[index]
                    
                    if inspect_type == self.selection_metadata_name:
                        
                        #Hartweg: Erstmal keine Selection
                        #prefix = "selection"
                        prefix = "hover"
                        
                    else:
                        prefix = "hover"
                        
                        if self.label == None:
                            #if self.label.data_point != (index_data[index[-1]], value_data[index[-1]]):
                            #Find the right position for  the information panel:
                            if screen_pts[0][1] > plot.bounds[1]/2:
                                label_position = "bottom "
                            else:
                                label_position = "top "
                                
                            if screen_pts[0][0] > plot.bounds[0]/2:
                                label_position = label_position + "left"
                            else:
                                label_position = label_position + "right"
                                   
                                                   
                            labIdx = index[-1] 
                            self.labelIndex =   labIdx                                                 
                            self.label = DataLabel(component=plot, data_point=(index_data[labIdx], value_data[labIdx]),
                                              label_position = label_position, padding=30,
                                              bgcolor = "lightgray",
                                              border_visible=False,
                                              show_label_coords = False)
                            #Collect information for output:
                   
                            self.label.label_text = ""#"Eigenvalue no. %g", % (labIdx)
                            self.label.label_text = self.label.label_text + "Eigenvalue no. %s" % (labIdx)
                            #'eigenvalue %.7g: %.7g +%.7g *i \nfrequency: %.5s Hz' % (evClicked, x, y, frequency) 
                            self.label.label_text = self.label.label_text + "\n %g +i*%g" % (index_data[labIdx], value_data[labIdx])
                            self.label.label_text = self.label.label_text + "\nFrequency: %.5s Hz" % (self.frequencies[labIdx])
                            if self.damping[labIdx]>0:
                                self.label.label_text = self.label.label_text + "\nDamping: %.5s" % self.damping[labIdx]
                            else:
                                self.label.label_text = self.label.label_text + "\nExcitation: %.5s" % self.damping[labIdx]
                            if self.damping[labIdx]<=0:
                                self.label.label_text = self.label.label_text + "\nNot Stable"
                            else:
                                self.label.label_text = self.label.label_text + "\nStable"                                     
                            if self.observability[labIdx]>0:
                                self.label.label_text = self.label.label_text + "\nObservable"
                            else:
                                self.label.label_text = self.label.label_text + "\nNot observable"           
                            if self.controllability[labIdx]>0:
                                self.label.label_text = self.label.label_text + "\nControllable"
                            else:
                                self.label.label_text = self.label.label_text + "\nNot controllable"                               
                            
                            plot.overlays.append(self.label)
                            tool = DataLabelTool(self.label, drag_button="right", auto_arrow_root=True)
                            self.label.tools.append(tool) 

                        self._render_at_indices(gc, screen_pts, prefix)
                elif prefix != "hover":
                    if self.label != None:
                        plot.overlays.pop(-1)#=last element
                        self.label = None
                        self.labelIndex = 999999
                if  len(index)>0:
                    if self.labelIndex != index[-1]:
                        if self.label != None:
                            print "delete label"
                            plot.overlays.pop(-1)#=last element
                            self.label = None     
                            self.labelIndex = 9999999                  
                    
        return

    def _render_at_indices(self, gc, screen_pts, inspect_type):
        """ screen_pt should always be a list """
        self._render_marker_at_indices(gc, screen_pts, inspect_type)

    def _render_marker_at_indices(self, gc, screen_pts, prefix, sep="_"):
        """ screen_pt should always be a list """
        if len(screen_pts) == 0:
            return

        
        plot = self.component

        mapped_attribs = ("color", "outline_color", "marker")
        other_attribs = ("marker_size", "line_width")
        kwargs = {}
        for attr in mapped_attribs + other_attribs:
            if attr in mapped_attribs:
                # Resolve the mapped trait
                valname = attr + "_"
            else:
                valname = attr

            tmp = getattr(self, prefix+sep+valname)
            if tmp is not None:
                kwargs[attr] = tmp
            else:
                kwargs[attr] = getattr(plot, valname)

        # If the marker type is 'custom', we have to pass in the custom_symbol
        # kwarg to render_markers.
        if kwargs.get("marker", None) == "custom":
            kwargs["custom_symbol"] = plot.custom_symbol

        with gc:
            gc.clip_to_rect(plot.x, plot.y, plot.width, plot.height)
            render_markers(gc, screen_pts, **kwargs)


    def _draw_overlay(self, gc, view_bounds=None, mode="normal"):
        self.overlay(self.component, gc, view_bounds, mode)

    def _component_changed(self, old, new):
        #print "hover on or out"
        if old:
            old.on_trait_change(self._ds_changed, 'index', remove=True)
            if hasattr(old, "value"):
                old.on_trait_change(self._ds_changed, 'value', remove=True)
        if new:
            for dsname in ("index", "value"):
                if not hasattr(new, dsname):
                    continue
                new.on_trait_change(self._ds_changed, dsname)
                if getattr(new, dsname):
                    self._ds_changed(new, dsname, None, getattr(new,dsname))
        return

    def _ds_changed(self, object, name, old, new):
        if old:
            old.on_trait_change(self.metadata_changed, 'metadata_changed', remove=True)
        if new:
            new.on_trait_change(self.metadata_changed, 'metadata_changed')
        return


