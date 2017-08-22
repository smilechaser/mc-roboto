'''
'''

from observer import Listener
from packet_event import PacketEvent
from protocol import State, Direction
from item import Item


class InventoryReactor:

    def __init__(self, packet_factory, connection):

        self.connection = connection

        RESPONSE_PACKETS = (
            'held_item_slot', 'block_dig'
        )

        for name in RESPONSE_PACKETS:

            prop_name = name + '_packet'

            packet = packet_factory.get_by_name(State.PLAY,
                                                Direction.TO_SERVER, name)

            setattr(self, prop_name, packet)

        self._active_hotbar_slot = 0

        self.slots = {}

    @property
    def active_hotbar_slot(self):

        return self._active_hotbar_slot

    @active_hotbar_slot.setter
    def active_hotbar_slot(self, slot_num):

        his = self.held_item_slot_packet()
        his.fields.slotId = slot_num
        self.connection.send(his)

        self._active_hotbar_slot = slot_num

    def swap_hands(self):

        bd = self.block_dig_packet()

        bd.fields.status = 6
        bd.fields.location.x = 0
        bd.fields.location.y = 0
        bd.fields.location.z = 0
        bd.fields.face = 0
        self.connection.send(bd)

    def drop(self, all=False):

        bd = self.block_dig_packet()

        if all:
            bd.fields.status = 3
        else:
            bd.fields.status = 4

        bd.fields.location.x = 0
        bd.fields.location.y = 0
        bd.fields.location.z = 0
        bd.fields.face = 0

        self.connection.send(bd)

    @Listener(PacketEvent, area=State.PLAY, key='held_item_slot')
    def on_held_item_change(self, event):

        self._active_hotbar_slot = event.packet.fields.slot

    @Listener(PacketEvent, area=State.PLAY, key='set_slot')
    def on_set_slot(self, event):

        packet = event.packet

#        import pprint

#         pprint.pprint({
#             'event': event,
#             'windowId': packet.fields.windowId,
#             'slot': packet.fields.slot,
#             'item': {
#                 'block_id': packet.fields.item.block_id,
#                 'count': packet.fields.item.item_count,
#                 'damage': packet.fields.item.item_damage
#             }
#         })

        fields = packet.fields
        item = fields.item

        if item.block_id == -1:
            # clear the slot
            self.slots.pop(fields.slot, None)
        else:

            self.slots[fields.slot] = Item(
                block_id=item.block_id,
                count=item.item_count,
                damage=item.item_damage,
                data=item.nbt
            )
