class TwoWayDict:
    """A bidirectional dictionary that maintains one-to-one mappings."""
    def __init__(self, initial_dict=None):
        self.forward = {} # Key -> Value
        self.backward = {} # Value -> Key
        if initial_dict:
            for key, value in initial_dict.items():
                self[key] = value

    def __setitem__(self, key, value):
        # Ensure one-to-one mapping by removing existing entries with the same key or value
        if key in self.forward:
            del self.backward[self.forward[key]]
        if value in self.backward:
            del self.forward[self.backward[value]]
        
        self.forward[key] = value
        self.backward[value] = key

    def __getitem__(self, key):
        # Try getting the value from the forward dict, otherwise try getting the key from the backward dict
        try:
            return self.forward[key]
        except KeyError:
            return self.backward[key]

    def __delitem__(self, key):
        # Delete from both dictionaries
        if key in self.forward:
            value = self.forward[key]
            del self.forward[key]
            del self.backward[value]
        elif key in self.backward:
            value = self.backward[key] # Actually this would be the key of the value
            del self.backward[key] # Delete value from backward
            del self.forward[value] # Delete key from forward
        else:
            raise KeyError(key)

    def __len__(self):
        return len(self.forward)

    def __repr__(self):
        return f"TwoWayDict({self.forward})"