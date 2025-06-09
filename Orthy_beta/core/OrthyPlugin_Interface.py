class OrthyPlugin:
    """Interface for Orthy plugins."""

    def get_name(self):
        """Return the name of the plugin."""
        raise NotImplementedError("Method not implemented.")

    def get_btn_configs(self):
        """Return button configurations for the plugin."""
        raise NotImplementedError("Method not implemented.")

    def load(self):
        """Load the plugin resources."""
        raise NotImplementedError("Method not implemented.")

    def unload(self):
        """Unload the plugin resources."""
        raise NotImplementedError("Method not implemented.")