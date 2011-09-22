from .models import Option, CartItemOption
from django.db.models import Q
from shop.models.cartmodel import CartItem
from shop.models.productmodel import Product
from shop.views import ShopDetailView
from shop.util.cart import get_or_create_cart
from shop.views.cart import CartDetails
from shop_simplevariations.models import TextOption, CartItemTextOption
from shop_simplevariations.forms import SimpleVariationsForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _ 

class SimplevariationCartDetails(CartDetails):
    """Cart view that answers GET and POSTS request."""

    def post(self, *args, **kwargs):
        product_id = self.request.POST['add_item_id']
        product = Product.objects.get(pk=product_id)
        form = SimpleVariationsForm(product, self.request.POST)
        if form.is_valid():
            data = form.cleaned_data
        else:
            default_message = _(u'You must select some options')
            next_url = self.request.POST.get('next', reverse('cart'))
            message = self.request.POST.get('error_message', default_message)
            url = u'%s?message=%s' % (next_url, message)
            return HttpResponseRedirect(url)

        ###
        #it starts similar to the original post method
        product_id = data['add_item_id']
        product_quantity = data['add_item_quantity']
        if not product_quantity:
            product_quantity = 1
        cart_object = get_or_create_cart(self.request)

        #now we need to find out which options have been chosen by the user
        option_ids = []
        text_option_ids = {} # A dict of {TextOption.id:CartItemTextOption.text}
        for key in self.request.POST.keys():
            if key.startswith('add_item_option_group_') and self.request.POST[key]!='':
                option_ids.append(self.request.POST[key])
            elif key.startswith('add_item_text_option_'):
                id = key.split('add_item_text_option_')[1]
                text_option_ids.update({id:self.request.POST[key]})

        #now we need to find out if there are any cart items that have the exact
        #same set of options
        qs = CartItem.objects.filter(cart=cart_object).filter(product=product)
        found_cartitem_id = None
        merge = False
        for cartitem in qs:
            # for each CartItem in the Cart, get it's options and text options
            cartitemoptions = CartItemOption.objects.filter(
                cartitem=cartitem, option__in=option_ids
                )
                
            cartitemtxtoptions = CartItemTextOption.objects.filter(
                text_option__in=text_option_ids.keys(),
                text__in=text_option_ids.values()
                )
            
            if len(cartitemoptions) + len(cartitemtxtoptions) == (len(option_ids) + len(text_option_ids)):
                found_cartitem_id = cartitem.id
                merge = True
                break

        #if we found a CartItem object that has the same options, we need
        #to select this one instead of just any CartItem that belongs to this
        #cart and this product.
        if found_cartitem_id:
            qs = CartItem.objects.filter(pk=found_cartitem_id)

        cart_item = cart_object.add_product(
            product, product_quantity, merge=merge, queryset=qs)
        cart_object.save()
        return self.post_success(product, cart_item)

    def post_success(self, product, cart_item):
        super(SimplevariationCartDetails, self).post_success(product, cart_item)
        #if this cart item already has an option set we don't need to do
        #anything because an existing option set will never change. if we got a
        #set of different options, that would become a new CartItem.
        if cart_item.cartitemoption_set.exists():
            return self.success()

        post = self.request.POST
        for key in self.request.POST.keys():
            if key.startswith('add_item_option_group_') and post[key]:
                option = Option.objects.get(pk=int(post[key]))
                cartitem_option = CartItemOption()
                cartitem_option.cartitem = cart_item
                cartitem_option.option = option
                cartitem_option.save()
            elif key.startswith('add_item_text_option_'):
                id = key.split('add_item_text_option_')[1]
                txt = self.request.POST[key]
                txt_opt = TextOption.objects.get(pk=id)
                cito = CartItemTextOption()
                cito.text_option = txt_opt
                cito.text = txt
                cito.cartitem = cart_item
                cito.save()
                
        return self.success()


class ShopDetailWithVariationsView(ShopDetailView):
    form_class = SimpleVariationsForm
    
    def get_form_class(self):
        return self.form_class

    def get_context_data(self, *args, **kwargs):

        # Call the base implementation first to get a context
        context = super(ShopDetailView, self).get_context_data(*args, **kwargs)
        form_class = self.get_form_class()
        form = form_class(self.object)
        context['form'] = form
        return context
