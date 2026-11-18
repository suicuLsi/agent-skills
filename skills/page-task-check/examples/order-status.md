# Check whether an order status was saved

Copy the prompt below into a session with `page-task-check` installed. The order, environment, and observations are fictional.

## Prompt

> Use `page-task-check` for a read-only acceptance review of an order workbench. The task is to move a packed order to Ready and find it there after a page reload. Use the supplied observations for your verdict. Report the result, the evidence, and the smallest follow-up check.
>
> - The build passed. In a test environment, an operator opened the board and found order `ORD-104` under **Packing**.
> - The operator dragged `ORD-104` to **Ready**. The card moved immediately and the page displayed **Saved**.
> - The save request returned HTTP `503`. The page kept the card in **Ready** until reload.
> - Reloading the board put `ORD-104` back in **Packing**. The supplied evidence covers the pointer path only.

## Expected result

The task **fails**. The move appeared to succeed, but the save request returned `503` and the order reverted on reload. The **Saved** message can lead an operator to act on a status that was never stored. The supplied observations leave keyboard operation unverified.

The smallest follow-up uses an authorized test order. Check that a confirmed save keeps the order in **Ready** after reload. On a failed save, check that the page displays a failure and shows or restores the last confirmed status. No additional operations are needed to assess the supplied evidence.
