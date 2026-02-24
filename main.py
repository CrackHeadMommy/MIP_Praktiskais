import game_state
import random
print("hello world")
# TODO:
# Lietas, kas obligāti jābūt kodā pēc PD1 norādēm:
# izvēlēties, kurš uzsāk spēli: cilvēks vai dators;
# izvēlēties, kuru algoritmu izmantos dators konkrētajā spēles reizē: Minimaksa algoritmu vai Alfa-beta algoritmu;
# izpildīt gājienus un redzēt izmaiņas spēles laukumā pēc gājienu (gan cilvēka, gan datora) izpildes;
# uzsākt spēli atkārtoti pēc kārtējās spēles pabeigšanas.

# obligāti ir jārealizē:
# spēles koka daļas glabāšana datu struktūras veidā (klases, saistītie saraksti, utt.)
# spēles koka ģenerēšana līdz noteiktajam līmenim atkarībā no spēles sarežģītības
# heiristiskā novērtējuma funkcijas izstrāde un tās pielietošana laikā, kad datoram ir jāveic gājiens
# Minimaksa algoritms un Alfa-beta algoritms (abiem ir jābūt realizētiem kā Pārlūkošana uz priekšu pār n-gājieniem)

######### Spēles iestatīšana #########
length = int(input("Ievadi skaitļu virknes garumu: "))
def get_random_sequence(length):
    sequence = []
    for _ in range(length):
        sequence.append(random.randint(1, 3))
    return sequence