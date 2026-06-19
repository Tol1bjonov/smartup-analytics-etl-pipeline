import os
from config import OUTPUT_DIR
from pipelines import products
from pipelines import natural_person
from pipelines import services
from pipelines import product_group
from pipelines import price_type
from pipelines import inventory_price
from pipelines import producers
from pipelines import legal_entity
from pipelines import person_group
from pipelines import workspaces
from pipelines import contracts
from pipelines import return_reason
from pipelines import order
from pipelines import returns
from pipelines import visit
from pipelines import (cross_movement, internal_movement, stocktaking,writeoff, warehouse_input, purchase, logistics)

os.makedirs(OUTPUT_DIR, exist_ok=True)



# products.run()
# natural_person.run()
# services.run()
# product_group.run()
# price_type.run()
# inventory_price.run()
# producers.run()
# legal_entity.run()
# person_group.run()
# workspaces.run()
# contracts.run()
# return_reason.run()  autenfikansiya xato beryapti
# order.run()
# returns.run()
# visit.run()
# cross_movement.run()  
# internal_movement.run()
# stocktaking.run()
# writeoff.run()
# warehouse_input.run()
# purchase.run()
logistics.run()

