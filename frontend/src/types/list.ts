export interface MyListItem {
  productId: number;
  productName: string;
  quantity: number;
  checked: boolean;
}

export interface MyListState {
  id: string;
  items: MyListItem[];
  createdAt: string;
}
