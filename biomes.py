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
            if 'frozen' in self.biome_tags:
                self.biome_title = 'frozen ocean'
            elif 'cold' in self.biome_tags:
                self.biome_title = 'arctic ocean'
            elif 'coastal' in self.biome_tags:
                self.biome_title = 'coastal waters'
            else:
                self.biome_title = 'ocean'

        else:
            # Arid biomes
            if 'arid' in self.biome_tags:
                if 'frozen' in self.biome_tags:
                    self.biome_title = 'tundra'
                elif 'forested' in self.biome_tags:
                    self.biome_title = 'savanna'
                elif 'cold' in self.biome_tags:
                    self.biome_title = 'arid steppe'
                elif 'light rain' in self.biome_tags or 'coastal' in self.biome_tags:
                    self.biome_title = 'arid scrubland'
                elif 'alpine' in self.biome_tags:
                    self.biome_title = 'arid peaks'
                elif 'hot' in self.biome_tags:
                    self.biome_title = 'high desert'
                else:
                    self.biome_title = 'low desert'

            # Dryland biomes
            elif 'dry' in self.biome_tags:
                if 'forested' in self.biome_tags:
                    if 'hot' in self.biome_tags:
                        self.biome_title = 'savanna'
                    elif 'coastal' in self.biome_tags:
                        self.biome_title = 'coastal dryland forest'
                    elif 'alpine' in self.biome_tags:
                        self.biome_title = 'dry alpine forest'
                    else:
                        self.biome_title = 'dryland forest'
                else:
                    if 'frozen' in self.biome_tags:
                        self.biome_title = 'tundra'
                    elif 'hot' in self.biome_tags:
                        self.biome_title = 'low desert'
                    elif 'alpine' in self.biome_tags:
                        self.biome_title = 'heath'
                    elif 'light rain' in self.biome_tags:
                        self.biome_title = 'steppe'
                    else:
                        self.biome_title = 'dry scrubland'

            # Humid biomes
            elif 'humid' in self.biome_tags:
                if 'forested' in self.biome_tags:
                    if 'hot' in self.biome_tags:
                        if 'heavy rain' in self.biome_tags:
                            self.biome_title = 'jungle'
                        else:
                            self.biome_title = 'tropical forest'
                    elif 'frozen' in self.biome_tags:
                        self.biome_title = 'frozen forest'
                    elif 'alpine' in self.biome_tags:
                        self.biome_title = 'alpine forest'
                    elif 'heavy rain' in self.biome_tags:
                        self.biome_title = 'rainforest'
                    else:
                        self.biome_title = 'temperate forest'
                elif 'plain' in self.biome_tags:
                    self.biome_title = 'flood plain'
                elif 'coastal' in self.biome_tags:
                    if 'cold' in self.biome_tags:
                        self.biome_title = 'cold scrubland coastline'
                    if 'heavy rain' not in self.biome_tags and 'light rain' not in self.biome_tags:
                        self.biome_title = 'sand dunes'
                    else:
                        self.biome_title = 'temperate coastline'
                else:
                    self.biome_title = 'meadow'

            # Damp biomes
            elif 'damp' in self.biome_tags:
                if 'forested' in self.biome_tags:
                    if 'hot' in self.biome_tags and 'heavy rain' in self.biome_tags:
                        self.biome_title = 'jungle'
                    elif 'frozen' in self.biome_tags:
                        self.biome_title = 'frozen forest'
                    elif 'heavy rain' in self.biome_tags:
                        self.biome_title = 'rainforest'
                    else:
                        self.biome_title = 'wetland forest'
                elif 'plain' in self.biome_tags:
                    if 'coastal' in self.biome_tags:
                        self.biome_title = 'coastal swamp'
                    elif 'landlocked' in self.biome_tags:
                        self.biome_title = 'bog'
                    elif 'cold' in self.biome_tags:
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
        elif self.temp_low < self.cell.settings.temps_freezing:
            tag_cloud.append('cold')
        elif self.temp_peak > self.cell.settings.biome_desert_temp:
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

        # Otherwise determine if they should house forests
        elif (self.annual_rainfall + self.flowrate_low) * self.cell.settings.biome_water_flow_effect > \
                self.cell.settings.biome_forest_water_req:
            tag_cloud.append('forested')

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
                    break
            landlocked = False

        if landlocked:
            tag_cloud.append('landlocked')

        # Determine heavy rainfall tag
        if self.annual_rainfall > self.cell.settings.biome_heavy_rainfall:
            tag_cloud.append('heavy rain')
        elif self.annual_rainfall > self.cell.settings.biome_light_rainfall:
            tag_cloud.append('light rain')

        return tag_cloud

    def get_color(self):
        """Uses the biome title to produce a composite color from the biome color and several environmental factors"""
        stg = self.cell.settings  # alias

        alt_tint = (200 * self.cell.altitude * stg.biome_alt_tint_strength) - (100 * stg.biome_alt_tint_strength)
        temp_tint = ((((self.temp_low + self.temp_peak) / 2) - self.cell.settings.temps_lowest) / (self.cell.settings.temps_highest - self.cell.settings.temps_lowest))
        temp_tint = (200 * temp_tint * stg.biome_temp_tint_strength) - (100 * stg.biome_temp_tint_strength)

        r = (stg.biome_colors[self.biome_title][0] * stg.biome_tint_strength) + alt_tint + temp_tint
        g = (stg.biome_colors[self.biome_title][1] * stg.biome_tint_strength) + alt_tint
        b = (stg.biome_colors[self.biome_title][2] * stg.biome_tint_strength) + alt_tint - temp_tint

        if r > 255:
            r = 255
        elif r < 0:
            r = 0
        if g > 255:
            g = 255
        elif g < 0:
            g = 0
        if b > 255:
            b = 255
        elif b < 0:
            b = 0

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

