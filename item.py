class Item:

    def __init__(self, block_id, count, damage, data):

        self.block_id = block_id
        self.count = count
        self.damage = damage
        self.data = data

    def __str__(self):

        return 'block: {:3d}, count: {:2d}, damage: {}'.format(self.block_id, self.count, self.damage)
