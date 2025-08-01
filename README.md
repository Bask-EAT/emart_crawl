uvicorn main1:app --reload --port 8420

주요기능

1.categories.json 생성

2.categories.json으로 상품json 추출

3.상품json으로 상품img 추출

4.루트페이지에서 상세 설정 ui 지원

5.ㅇㅇ

```
상품json 추출결과 예시
{
    "category": "Fruits",
    "product_name": "데일리 사과 1.5kg (4~8입) 봉",
    "product_address": "https://emart.ssg.com/item/itemView.ssg?itemId=1000633289875&siteNo=7009&salestrNo=2551",
    "original_price": "18900",
    "selling_price": "18900",
    "image_url": "https://sitem.ssgcdn.com/75/98/28/item/1000633289875_i1_290.jpg",
    "quantity": "100g 당 1,260원",
    "out_of_stock": "N"
}
```
