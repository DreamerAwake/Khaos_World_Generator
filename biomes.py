class Biome:
    """A class for all biome objects. Used to store and process data about a cell's biome.
    Biomes are generated after a number of years of world simulation have occured. To assure that the results
    are accurate, erosion should not occur after biomes have been set, without again regenerating the biomes."""
    def __init__(self, parent_cell):
        self.cell = parent_cell
        last_4_seasons = [parent_cell.last_spring,
                          parent_cell.last_summer,
                          parent_cell.last_autumn,
                          parent_cell.last_winter]

        # Basic biome data
        self.biome_title = 'undefined land'

        # Temperature data
        self.temp_peak, self.temp_low = self.get_parent_temps(last_4_seasons)
        self.average_humidity = self.get_parent_ave_humidity(last_4_seasons)
        self.annual_rainfall = self.cell.last_winter.rainfall_this_year
        self.flowrate_peak, self.flowrate_low = self.get_parent_flowrate(last_4_seasons)

        # Fetch the biome here
        self.biome_tags = self.get_biome_tags()
        self.get_biome()

    def get_biome(self):
        """Determines the biome for the cell based on aggregated data."""
        # Aquatic biomes
        if 'aquatic' in self.biome_tags:
            if self.temp_peak < self.cell.settings.temps_freezing:
                self.biome_title = 'frozen ocean'
            elif self.temp_low < self.cell.settings.temps_freezing:
                self.biome_title = 'arctic ocean'
            elif 'coastal' in self.biome_tags:
                self.biome_title = 'coastal waters'
            else:
                self.biome_title = 'ocean'

        # Terrain biomes
        else:
            # First add arid biomes
            if 'arid' in self.biome_tags:
                if self.temp_peak > self.cell.settings.biome_desert_temp:
                    self.biome_title = 'high desert'
                elif self.temp_low > self.cell.settings.temps_freezing:
                    self.biome_title = 'arid steppe'
                elif 'frozen' not in self.biome_tags:
                    self.biome_title = 'cold desert'
                else:
                    self.biome_title = 'tundra'

            # Dryland biomes
            elif 'dry' in self.biome_tags:
                if self.annual_rainfall + self.flowrate_low < self.cell.settings.biome_forest_water_req * 2:
                    if 'coastal' in self.biome_tags:
                        self.biome_title = 'sand dunes'
                    else:
                        if 'hot' in self.biome_tags:
                            self.biome_title = 'savanna'
                        else:
                            self.biome_title = 'dry scrubland'
                elif 'coastal' in self.biome_tags:
                    self.biome_title = 'coastal dryland forest'
                elif 'alpine' in self.biome_tags:
                    self.biome_title = 'dry alpine forest'
                else:
                    self.biome_title = 'dryland forest'

            # Average humidity biomes
            elif 'humid' in self.biome_tags:
                if self.annual_rainfall + self.flowrate_low < self.cell.settings.biome_forest_water_req:
                    if 'plain' in self.biome_tags:
                        self.biome_title = 'flood plain'
                    elif 'coastal' in self.biome_tags:
                        if self.temp_low < self.cell.settings.temps_freezing:
                            self.biome_title = 'cold scrubland coastline'
                        else:
                            self.biome_title = 'temperate coastline'
                    else:
                        self.biome_title = 'meadows'

                elif self.annual_rainfall + self.flowrate_low > self.cell.settings.biome_rainforest_req * 2:
                    if abs(self.cell.y) > self.cell.settings.atmo_tropics_extent:
                        self.biome_title = 'tropical rainforest'
                    elif self.temp_peak < self.cell.settings.temps_freezing:
                        self.biome_title = 'frozen forest'
                    else:
                        self.biome_title = 'rainforest'
                elif self.cell.altitude > self.cell.settings.biome_alpine_line:
                    self.biome_title = 'alpine forest'
                else:
                    self.biome_title = 'temperate forest'

            # Damp biomes
            elif 'damp' in self.biome_tags:
                if self.annual_rainfall + self.flowrate_low > self.cell.settings.biome_rainforest_req:
                    if abs(self.cell.y) < self.cell.settings.atmo_tropics_extent:
                        self.biome_title = 'tropical rainforest'
                    elif self.temp_peak < self.cell.settings.temps_freezing:
                        self.biome_title = 'frozen forest'
                    else:
                        self.biome_title = 'rainforest'
                elif self.annual_rainfall + self.flowrate_low > self.cell.settings.biome_forest_water_req:
                    if abs(self.cell.y) < self.cell.settings.atmo_tropics_extent:
                        if self.temp_peak > self.cell.settings.temps_equatorial:
                            self.biome_title = 'jungle'
                        else:
                            self.biome_title = 'tropical forest'
                    elif 'frozen' in self.biome_tags:
                        self.biome_title = 'frozen forest'
                    else:
                        self.biome_title = 'wetland forest'
                elif 'plain' in self.biome_tags:
                    if 'coastal' in self.biome_tags:
                        self.biome_title = 'coastal swamp'
                    elif 'landlocked' in self.biome_tags:
                        self.biome_title = 'bog'
                    elif self.temp_low < self.cell.settings.temps_freezing:
                        self.biome_title = 'cold marsh'
                    else:
                        self.biome_title = 'marsh'
                else:
                    self.biome_title = 'swamp'
            else:
                self.biome_title = 'undefined land'

    def get_biome_tags(self):
        """Biome tags are used to determine what reducable properties are present in a biome."""
        tag_cloud = []

        # Get temp tags
        if self.temp_peak < self.cell.settings.temps_freezing:
            tag_cloud.append('frozen')
        elif self.temp_peak > self.cell.settings.temps_equatorial:
            tag_cloud.append('hot')

        # Get height tags
        if self.cell.altitude > self.cell.settings.biome_alpine_line:
            tag_cloud.append('alpine')
        elif self.cell.altitude < self.cell.settings.wtr_sea_level + self.cell.settings.biome_plains_height:
            tag_cloud.append('plain')

        # Determine humidity
        if self.average_humidity > self.cell.settings.biome_humid_high:
            tag_cloud.append('damp')
        elif self.average_humidity > self.cell.settings.biome_humid_low:
            tag_cloud.append('humid')
        elif self.average_humidity > self.cell.settings.biome_arid:
            tag_cloud.append('dry')
        else:
            tag_cloud.append('arid')

        # Mark underwater biomes with 'aquatic'
        if self.cell.altitude < self.cell.settings.wtr_sea_level:
            tag_cloud.append('aquatic')

        # Determine if the biome is landlocked or coastal
        landlocked = True
        if 'aquatic' not in tag_cloud:
            for cell_neighbor in self.cell.neighbors.keys():
                if cell_neighbor.altitude < self.cell.settings.wtr_sea_level:
                    tag_cloud.append('coastal')
                    landlocked = False
                    break
        else:
            for cell_neighbor in self.cell.neighbors.keys():
                if cell_neighbor.altitude > self.cell.settings.wtr_sea_level:
                    tag_cloud.append('coastal')
            landlocked = False

        if landlocked:
            tag_cloud.append('landlocked')

        return tag_cloud

    def get_color(self):
        """Uses the biome title to produce a composite color from the biome color and several environmental factors"""
        r = self.cell.settings.biome_colors[self.biome_title][0]
        g = self.cell.settings.biome_colors[self.biome_title][1]
        b = self.cell.settings.biome_colors[self.biome_title][2]

        return r, g, b

    def get_parent_ave_humidity(self, last_4_seasons):
        """Looks into the parent cell and averages the last 4 seasons' humidity readings."""
        humidity = 0.0

        for season in last_4_seasons:
            humidity += season.humidity

        humidity /= 4

        return humidity

    def get_parent_flowrate(self, last_4_seasons):
        """Gets the flowrate from the parent cell's season history"""
        highest_found = 0
        lowest_found = 60000
        for season in last_4_seasons:
            if season.average_flow > highest_found:
                highest_found = season.average_flow
            if season.average_flow < lowest_found:
                lowest_found = season.average_flow

        return highest_found, lowest_found

    def get_parent_temps(self, last_4_seasons):
        """Looks into parent cell season data and finds highs and lows."""
        highest_found = self.cell.settings.temps_lowest
        lowest_found = self.cell.settings.temps_highest

        for season in last_4_seasons:
            if season.temperature > highest_found:
                highest_found = season.temperature
            if season.temperature < lowest_found:
                lowest_found = season.temperature

        return highest_found, lowest_found

